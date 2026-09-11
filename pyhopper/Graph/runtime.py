from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from importlib import import_module
from pathlib import Path
import re
from typing import Any, Callable

from pyhopper.Core.Component import Component, ComponentResult, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Graph.catalog import literal_input_names
from pyhopper.Utils.Exporters import export_glb_with_manifest


ENTRYPOINT_NAME = "build_graph_definition"
PREVIEW_OUTPUTS_ENTRYPOINT = "build_graph_preview_outputs"
NODE_OUTPUTS_ENTRYPOINT = "build_graph_node_outputs"
MERGE_COMPONENT_KEY = "pyhopper.Components.Sets.Tree.Merge.Merge"

# Tree-level port operations map to DataTree methods ...
PORT_OP_METHODS: dict[str, str] = {
    "Graft": "graft",
    "Simplify": "simplify",
    "Flatten": "flatten",
    "Reverse": "reverse",
}
# ... while item-level ones (Grasshopper's Reparameterize acts on curve domains)
# map to a (module, function) applied to the whole tree.
PORT_OP_FUNCTIONS: dict[str, tuple[str, str]] = {
    "Reparametrize": ("pyhopper.Utils.Curves", "reparametrize_tree"),
}
VALID_PORT_OPERATIONS = frozenset(PORT_OP_METHODS) | frozenset(PORT_OP_FUNCTIONS)


class GraphCompilerValidationError(Exception):
    def __init__(self, errors: list[dict[str, str]]) -> None:
        self.errors = errors
        message = errors[0]["message"] if errors else "Graph validation failed"
        super().__init__(message)


@dataclass(frozen=True)
class ResolvedNode:
    node_id: str
    component_key: str
    component_cls: type[Component] | None
    inputs: list[InputParam]
    outputs: list[OutputParam]
    preview_enabled: bool
    settings: dict[str, Any]
    values: dict[str, Any]
    variadic_inputs: bool
    port_operations: dict[str, str]
    object_atom: dict[str, Any] | None = None
    object_transform: dict[str, Any] | None = None


@dataclass(frozen=True)
class ValidatedEdge:
    edge_id: str
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str


@dataclass(frozen=True)
class CompiledGraph:
    graph_id: str
    source: str
    entrypoint: str = ENTRYPOINT_NAME
    preview_outputs_entrypoint: str = PREVIEW_OUTPUTS_ENTRYPOINT
    node_outputs_entrypoint: str = NODE_OUTPUTS_ENTRYPOINT
    preview_node_ids: tuple[str, ...] = ()


def _truncate_preview_text(value: str, limit: int = 120) -> str:
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def serialize_preview_value(value: Any) -> dict[str, Any]:
    if isinstance(value, ComponentResult):
        primary_output_name = value.output_names[0] if value.output_names else "result"
        return serialize_preview_value(value.output(primary_output_name))

    if isinstance(value, DataTree):
        branches: list[dict[str, Any]] = []
        item_count = 0
        for path, branch in value.branches():
            items = [
                {"index": index, "value": _truncate_preview_text(repr(item))}
                for index, item in enumerate(branch)
            ]
            item_count += len(items)
            branches.append({"path": str(path), "items": items})
        return {
            "kind": "data-tree",
            "branch_count": len(branches),
            "item_count": item_count,
            "branches": branches,
        }

    return {
        "kind": "value",
        "value": _truncate_preview_text(repr(value)),
    }


def _error(path: str, message: str, code: str = "invalid_graph") -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _snake_case(value: str) -> str:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    return normalized or "component"


def _component_name(component_cls: type[Component] | None) -> str:
    return component_cls.__name__ if component_cls is not None else "ObjectReference"


def _resolve_component(component_key: str) -> type[Component]:
    module_name, _, class_name = component_key.rpartition(".")
    if not module_name or not class_name:
        raise ImportError(f"Invalid component key '{component_key}'")

    module = import_module(module_name)
    component_cls = getattr(module, class_name)
    if not isinstance(component_cls, type) or not issubclass(component_cls, Component):
        raise TypeError(f"{component_key} is not a pyhopper Component")
    return component_cls


def _literal_expression(value: Any) -> str:
    if isinstance(value, bool):
        return repr(value)
    if isinstance(value, (int, float)):
        return repr(float(value) if isinstance(value, float) else value)
    if value is None:
        return "None"
    if isinstance(value, str):
        return repr(value)
    raise ValueError(f"Unsupported literal value: {type(value).__name__}")


def _output_expression(variable_name: str, port_name: str, primary_output_name: str) -> str:
    if port_name == primary_output_name:
        return variable_name
    if port_name.isidentifier():
        return f"{variable_name}.{port_name}"
    return f"{variable_name}.output({port_name!r})"


def _apply_port_operation(expr: str, op_name: str | None, imports: set[tuple[str, str]]) -> str:
    """Wrap *expr* in the code for a port operation, registering any import it needs."""
    if not op_name:
        return expr
    method = PORT_OP_METHODS.get(op_name)
    if method:
        return f"{expr}.{method}()"
    module_name, function_name = PORT_OP_FUNCTIONS[op_name]
    imports.add((module_name, function_name))
    return f"{function_name}({expr})"


def _source_expression(
    edge: ValidatedEdge,
    port_expressions: dict[tuple[str, str], str],
    target_node: ResolvedNode,
    target_port: str,
    imports: set[tuple[str, str]],
) -> str:
    """Expression for the value arriving on *target_port* through *edge* (input op applied)."""
    expr = port_expressions[(edge.source_node_id, edge.source_port)]
    return _apply_port_operation(expr, target_node.port_operations.get(f"input:{target_port}"), imports)


# ── Authored values ────────────────────────────────────────────────
# Components declare what a person authors on a node: ``settings_schema`` for
# call-time ``_settings`` and ``authored_values`` for data the compiler bakes
# into the source; ``authored_emit`` names the strategy below that does so.
# Both schemas share one vocabulary of types.

SCHEMA_TYPE_CHECKS: dict[str, Callable[[Any], bool]] = {
    "float": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "int": lambda value: (isinstance(value, int) and not isinstance(value, bool)) or (isinstance(value, float) and value.is_integer()),
    "bool": lambda value: type(value) is bool,
    "string": lambda value: isinstance(value, str),
    "choice": lambda value: isinstance(value, str),
    "list": lambda value: isinstance(value, list),
}
SCHEMA_TYPE_LABELS: dict[str, str] = {
    "float": "numeric",
    "int": "an integer",
    "bool": "boolean",
    "string": "a string",
    "choice": "a string",
    "list": "a list",
}


def _authored_schema(component_cls: type[Component] | None) -> dict[str, dict[str, Any]]:
    schema = getattr(component_cls, "authored_values", None) if component_cls is not None else None
    return schema if isinstance(schema, dict) else {}


def _values_schema(component_cls: type[Component] | None) -> dict[str, dict[str, Any]]:
    """Everything ``values`` may hold: inline literals on literal-capable inputs (a wire on the
    same input wins), refined by the declared authored values."""
    return {**literal_input_names(component_cls), **_authored_schema(component_cls)}


def _settings_schema(component_cls: type[Component] | None) -> dict[str, dict[str, Any]]:
    schema = getattr(component_cls, "settings_schema", None) if component_cls is not None else None
    return schema if isinstance(schema, dict) else {}


def _coerce_to_schema(spec: dict[str, Any], value: Any) -> Any:
    """Bring *value* to the Python type its spec declares; strings and lists pass through."""
    kind = spec.get("type")
    if kind == "float":
        return float(value)
    if kind == "int":
        return int(value)
    if kind == "bool":
        return bool(value)
    return value


def _validate_against_schema(
    path: str,
    section: str,
    data: dict[str, Any],
    schema: dict[str, dict[str, Any]],
    errors: list[dict[str, str]],
    *,
    strict: bool,
) -> None:
    """Type- and choice-check *data* against *schema*; unknown keys error only when *strict*."""
    for key, value in data.items():
        spec = schema.get(key)
        if not isinstance(spec, dict):
            if strict:
                noun = "authored value" if section == "values" else "setting"
                errors.append(_error(f"{path}.{section}.{key}", f"Unknown {noun} '{key}'"))
            continue
        kind = spec.get("type")
        check = SCHEMA_TYPE_CHECKS.get(kind)
        if check is not None and not check(value):
            errors.append(_error(f"{path}.{section}.{key}", f"'{key}' must be {SCHEMA_TYPE_LABELS[kind]}"))
        elif kind == "choice" and value not in spec.get("choices", ()):
            errors.append(_error(f"{path}.{section}.{key}", f"Unsupported {key} '{value}'"))


def _validate_node_authoring(
    path: str,
    component_cls: type[Component],
    settings: dict[str, Any],
    values: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    """Check a node's ``settings`` and ``values`` against what its component declares."""
    emit = getattr(component_cls, "authored_emit", None)
    if emit is not None and emit not in AUTHORED_EMITTERS:
        errors.append(_error(f"{path}.componentKey", f"{component_cls.__name__} declares unknown authored_emit '{emit}'"))
        return

    before = len(errors)
    values_schema = _values_schema(component_cls)
    if emit == "settings":
        # The settings dict reaches the constructor, so every key must be declared. Documents
        # from before slider settings existed stored the value under values[<primary output>].
        primary = component_cls.outputs[0].name if component_cls.outputs else "value"
        for key, value in values.items():
            if key != primary:
                errors.append(_error(f"{path}.values.{key}", f"{component_cls.__name__} stores authored values in settings"))
            elif not SCHEMA_TYPE_CHECKS["float"](value):
                errors.append(_error(f"{path}.values.{key}", "Slider values must be numeric"))
        _validate_against_schema(path, "settings", settings, _settings_schema(component_cls), errors, strict=True)
    else:
        if values_schema:
            _validate_against_schema(path, "values", values, values_schema, errors, strict=True)
        else:
            for key in values:
                errors.append(_error(f"{path}.values.{key}", f"{component_cls.__name__} has no authored values or literal inputs"))
        # settings the component never reads are ignored, declared ones must still type-check
        _validate_against_schema(path, "settings", settings, _settings_schema(component_cls), errors, strict=False)

    if len(errors) == before:
        for section, data in (("settings", settings), ("values", values)):
            for key, message in component_cls.validate_authored(section, data):
                errors.append(_error(f"{path}.{section}.{key}" if key else f"{path}.{section}", message))


@dataclass(frozen=True)
class EmitContext:
    """Everything an authored-value emitter needs to write one node's line."""

    node: ResolvedNode
    variable_name: str
    imports: set[tuple[str, str]]
    incoming_by_port: dict[tuple[str, str], list[ValidatedEdge]]
    port_expressions: dict[tuple[str, str], str]

    @property
    def schema(self) -> dict[str, dict[str, Any]]:
        """Declared authored values (an emitter's own keys)."""
        return _authored_schema(self.node.component_cls)

    @property
    def values_schema(self) -> dict[str, dict[str, Any]]:
        """Authored values plus literal-capable inputs — every key ``values`` may carry."""
        return _values_schema(self.node.component_cls)

    def authored(self, key: str) -> Any:
        """The node's value for *key*, else the declared default."""
        return self.node.values.get(key, self.values_schema.get(key, {}).get("default"))

    def typed(self, key: str) -> Any:
        """``authored(key)`` coerced to the type the schema declares."""
        return _coerce_to_schema(self.values_schema.get(key, {}), self.authored(key))

    def wired(self, input_name: str) -> bool:
        return bool(self.incoming_by_port.get((self.node.node_id, input_name)))

    def source(self, input_name: str) -> str:
        """Expression feeding *input_name* (its input port operation applied)."""
        edge = self.incoming_by_port[(self.node.node_id, input_name)][0]
        return _source_expression(edge, self.port_expressions, self.node, input_name, self.imports)

    def module_name(self) -> str:
        return self.node.component_key.rpartition(".")[0]

    def import_component(self) -> str:
        """Import the node's class and return its name."""
        module_name, _, class_name = self.node.component_key.rpartition(".")
        self.imports.add((module_name, class_name))
        return class_name


def _slider_value(node: ResolvedNode) -> float:
    output_name = node.outputs[0].name if node.outputs else "value"
    raw_value = node.settings.get("value", node.values.get(output_name))
    if isinstance(raw_value, bool):
        raise GraphCompilerValidationError(
            [_error(f"nodes[{node.node_id}].values.{output_name}", "Slider value must be numeric")]
        )
    if isinstance(raw_value, (int, float)):
        return float(raw_value)

    config_value = _settings_schema(node.component_cls).get("value", {}).get("default")
    if isinstance(config_value, (int, float)) and not isinstance(config_value, bool):
        return float(config_value)

    default_value = getattr(node.component_cls, "DEFAULT_VALUE", None)
    if isinstance(default_value, (int, float)) and not isinstance(default_value, bool):
        return float(default_value)

    return 0.0


def _emit_literal(ctx: EmitContext) -> str:
    """The single authored value becomes a one-item tree (Boolean Toggle)."""
    ctx.imports.add(("pyhopper.Core.DataTree", "DataTree"))
    key = next(iter(ctx.schema))
    return f"{ctx.variable_name} = DataTree.from_item({_literal_expression(ctx.typed(key))})"


def _emit_vector(ctx: EmitContext) -> str:
    """Authored ``x``/``y`` (and ``z`` when declared) become one AtomicVector (MD Slider)."""
    ctx.imports.add(("pyhopper.Core.Atoms", "AtomicVector"))
    ctx.imports.add(("pyhopper.Core.DataTree", "DataTree"))
    x = float(ctx.authored("x"))
    y = float(ctx.authored("y"))
    z = float(ctx.authored("z")) if "z" in ctx.schema else 0.0
    return f"{ctx.variable_name} = DataTree.from_item(AtomicVector({x!r}, {y!r}, {z!r}))"


def _emit_panel(ctx: EmitContext) -> str | None:
    """An unwired Panel is a text source; a wired one is an ordinary pass-through call."""
    node = ctx.node
    if not node.inputs or ctx.wired(node.inputs[0].name):
        return None
    ctx.imports.add(("pyhopper.Core.DataTree", "DataTree"))
    text = str(ctx.authored("text"))
    if bool(ctx.authored("multilineData")):
        ctx.imports.add((ctx.module_name(), "parse_panel_lines"))
        return f"{ctx.variable_name} = DataTree.from_list(parse_panel_lines({_literal_expression(text)}))"
    ctx.imports.add((ctx.module_name(), "parse_panel_text"))
    return f"{ctx.variable_name} = DataTree.from_item(parse_panel_text({_literal_expression(text)}))"


def _emit_graph_mapper(ctx: EmitContext) -> str | None:
    """The authored graph becomes the config of ``map_graph_tree`` over the wired input."""
    node = ctx.node
    if not node.inputs or not ctx.wired(node.inputs[0].name):
        return None
    ctx.imports.add((ctx.module_name(), "map_graph_tree"))
    expr = ctx.source(node.inputs[0].name)
    config = {key: ctx.typed(key) for key in ctx.schema}
    return f"{ctx.variable_name} = map_graph_tree({expr}, {config!r})"


def _emit_settings(ctx: EmitContext) -> str:
    """The node's settings travel into the constructor as ``_settings`` (Number Slider)."""
    node = ctx.node
    class_name = ctx.import_component()
    settings = dict(node.settings)
    output_name = node.outputs[0].name if node.outputs else "value"
    if output_name in node.values and "value" not in settings:
        settings["value"] = _slider_value(node)  # legacy documents: value stored under the output name
    return f"{ctx.variable_name} = {class_name}(_settings={settings!r})"


# ``authored_emit`` name → emitter. An emitter returns the node's line, or None to
# let the generic constructor call handle the node after all.
AUTHORED_EMITTERS: dict[str, Callable[[EmitContext], str | None]] = {
    "literal": _emit_literal,
    "vector": _emit_vector,
    "panel": _emit_panel,
    "graph_mapper": _emit_graph_mapper,
    "settings": _emit_settings,
}


def _sanitize_filename(graph_id: str) -> str:
    safe_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", graph_id).strip("-").lower()
    return safe_id or "graph"


def _validate_document(document: Any) -> tuple[str, dict[str, ResolvedNode], list[ValidatedEdge]]:
    errors: list[dict[str, str]] = []

    if not isinstance(document, dict):
        raise GraphCompilerValidationError([_error("", "Graph document must be a JSON object")])

    schema_version = document.get("schemaVersion")
    if schema_version != 2:
        errors.append(_error("schemaVersion", "Only schemaVersion 2 is supported"))

    graph_id = document.get("graphId")
    if not isinstance(graph_id, str) or not graph_id:
        errors.append(_error("graphId", "graphId must be a non-empty string"))

    viewport = document.get("viewport")
    if not isinstance(viewport, dict):
        errors.append(_error("viewport", "viewport must be an object"))
    else:
        for key in ("x", "y", "zoom"):
            if not isinstance(viewport.get(key), (int, float)) or isinstance(viewport.get(key), bool):
                errors.append(_error(f"viewport.{key}", f"viewport.{key} must be numeric"))

    raw_nodes = document.get("nodes")
    if not isinstance(raw_nodes, list):
        errors.append(_error("nodes", "nodes must be an array"))
        raw_nodes = []

    raw_edges = document.get("edges")
    if not isinstance(raw_edges, list):
        errors.append(_error("edges", "edges must be an array"))
        raw_edges = []

    raw_scene = document.get("scene")
    scene_objects: dict[str, Any] = {}
    if not isinstance(raw_scene, dict) or raw_scene.get("schemaVersion") not in {2, 3}:
        errors.append(_error("scene", "scene must be a schemaVersion 2 or 3 scene document"))
    elif not isinstance(raw_scene.get("objects"), dict):
        errors.append(_error("scene.objects", "scene.objects must be an object map"))
    else:
        scene_objects = raw_scene["objects"]

    resolved_nodes: dict[str, ResolvedNode] = {}
    seen_node_ids: set[str] = set()

    for index, raw_node in enumerate(raw_nodes):
        path = f"nodes[{index}]"
        if not isinstance(raw_node, dict):
            errors.append(_error(path, "Each node must be an object"))
            continue

        node_id = raw_node.get("id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(_error(f"{path}.id", "Node id must be a non-empty string"))
            continue
        if node_id in seen_node_ids:
            errors.append(_error(f"{path}.id", f"Duplicate node id '{node_id}'"))
            continue
        seen_node_ids.add(node_id)

        node_kind = raw_node.get("kind")
        if node_kind not in {"component", "object-reference"}:
            errors.append(_error(f"{path}.kind", "Node kind must be 'component' or 'object-reference'"))
            continue

        position = raw_node.get("position")
        if not isinstance(position, dict):
            errors.append(_error(f"{path}.position", "position must be an object"))
        else:
            for axis in ("x", "y"):
                if not isinstance(position.get(axis), (int, float)) or isinstance(position.get(axis), bool):
                    errors.append(_error(f"{path}.position.{axis}", f"position.{axis} must be numeric"))

        preview_enabled = raw_node.get("previewEnabled", True)
        if not isinstance(preview_enabled, bool):
            errors.append(_error(f"{path}.previewEnabled", "previewEnabled must be a boolean"))
            preview_enabled = True

        raw_values = raw_node.get("values", {})
        if not isinstance(raw_values, dict):
            errors.append(_error(f"{path}.values", "values must be an object"))
            continue
        values = dict(raw_values)

        raw_settings = raw_node.get("settings", {})
        if not isinstance(raw_settings, dict):
            errors.append(_error(f"{path}.settings", "settings must be an object"))
            continue
        settings = dict(raw_settings)

        raw_port_operations = raw_node.get("portOperations", {})
        if not isinstance(raw_port_operations, dict):
            errors.append(_error(f"{path}.portOperations", "portOperations must be an object"))
            raw_port_operations = {}
        port_operations: dict[str, str] = {}
        for port_name, op in raw_port_operations.items():
            if not isinstance(op, str) or op not in VALID_PORT_OPERATIONS:
                errors.append(_error(f"{path}.portOperations.{port_name}", f"Invalid port operation '{op}'"))
                continue
            port_operations[port_name] = op

        if node_kind == "object-reference":
            object_id = raw_node.get("objectId")
            scene_object = scene_objects.get(object_id) if isinstance(object_id, str) else None
            object_atom = scene_object.get("atom") if isinstance(scene_object, dict) else None
            object_tree = scene_object.get("tree") if isinstance(scene_object, dict) else None
            if not isinstance(object_atom, dict) and isinstance(object_tree, dict):
                branches = object_tree.get("branches")
                if isinstance(branches, list) and branches and isinstance(branches[0], dict):
                    items = branches[0].get("items")
                    if isinstance(items, list) and items and isinstance(items[0], dict):
                        object_atom = items[0]
            object_transform = scene_object.get("transform") if isinstance(scene_object, dict) else None
            transform_matrix = object_transform.get("matrix") if isinstance(object_transform, dict) else None
            if not isinstance(object_id, str) or not object_id:
                errors.append(_error(f"{path}.objectId", "objectId must be a non-empty string"))
                continue
            if not isinstance(object_atom, dict) or not isinstance(object_atom.get("type"), str):
                errors.append(_error(f"{path}.objectId", f"Scene object '{object_id}' does not exist or has no atom"))
                continue
            if (
                not isinstance(transform_matrix, list)
                or len(transform_matrix) != 16
                or any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in transform_matrix)
            ):
                errors.append(_error(f"{path}.objectId", f"Scene object '{object_id}' has no valid transform matrix"))
                continue
            resolved_nodes[node_id] = ResolvedNode(
                node_id=node_id,
                component_key="",
                component_cls=None,
                inputs=[],
                outputs=[OutputParam("geometry")],
                preview_enabled=preview_enabled,
                settings={},
                values={},
                variadic_inputs=False,
                port_operations=port_operations,
                object_atom=object_atom,
                object_transform={"type": "Transform", "matrix": transform_matrix},
            )
            continue

        component_key = raw_node.get("componentKey")
        if not isinstance(component_key, str) or not component_key:
            errors.append(_error(f"{path}.componentKey", "componentKey must be a non-empty string"))
            continue

        try:
            component_cls = _resolve_component(component_key)
        except Exception as exc:
            errors.append(_error(f"{path}.componentKey", f"Failed to resolve component '{component_key}': {exc}"))
            continue

        outputs = list(getattr(component_cls, "outputs", []))
        _validate_node_authoring(path, component_cls, settings, values, errors)

        resolved_nodes[node_id] = ResolvedNode(
            node_id=node_id,
            component_key=component_key,
            component_cls=component_cls,
            inputs=list(getattr(component_cls, "inputs", [])),
            outputs=outputs,
            preview_enabled=preview_enabled,
            settings=settings,
            values=values,
            variadic_inputs=bool(getattr(component_cls, "variadic_inputs", False)),
            port_operations=port_operations,
        )

    validated_edges: list[ValidatedEdge] = []
    seen_edge_ids: set[str] = set()

    for index, raw_edge in enumerate(raw_edges):
        path = f"edges[{index}]"
        if not isinstance(raw_edge, dict):
            errors.append(_error(path, "Each edge must be an object"))
            continue
        edge_id = raw_edge.get("id")
        if not isinstance(edge_id, str) or not edge_id:
            errors.append(_error(f"{path}.id", "Edge id must be a non-empty string"))
            continue
        if edge_id in seen_edge_ids:
            errors.append(_error(f"{path}.id", f"Duplicate edge id '{edge_id}'"))
            continue
        seen_edge_ids.add(edge_id)
        source_node_id = raw_edge.get("sourceNodeId")
        source_port = raw_edge.get("sourcePort")
        target_node_id = raw_edge.get("targetNodeId")
        target_port = raw_edge.get("targetPort")
        if not isinstance(source_node_id, str) or source_node_id not in resolved_nodes:
            errors.append(_error(f"{path}.sourceNodeId", f"Unknown source node '{source_node_id}'"))
            continue
        if not isinstance(target_node_id, str) or target_node_id not in resolved_nodes:
            errors.append(_error(f"{path}.targetNodeId", f"Unknown target node '{target_node_id}'"))
            continue
        if not isinstance(source_port, str) or not source_port:
            errors.append(_error(f"{path}.sourcePort", "sourcePort must be a non-empty string"))
            continue
        if not isinstance(target_port, str) or not target_port:
            errors.append(_error(f"{path}.targetPort", "targetPort must be a non-empty string"))
            continue
        source_outputs = {output.name for output in resolved_nodes[source_node_id].outputs}
        if source_port not in source_outputs:
            errors.append(_error(f"{path}.sourcePort", f"Output '{source_port}' does not exist on node '{source_node_id}'"))
            continue
        target_inputs = {input_param.name for input_param in resolved_nodes[target_node_id].inputs}
        if target_port not in target_inputs:
            errors.append(_error(f"{path}.targetPort", f"Input '{target_port}' does not exist on node '{target_node_id}'"))
            continue
        validated_edges.append(
            ValidatedEdge(
                edge_id=edge_id,
                source_node_id=source_node_id,
                source_port=source_port,
                target_node_id=target_node_id,
                target_port=target_port,
            )
        )

    incoming_by_port: dict[tuple[str, str], list[ValidatedEdge]] = {}
    for edge in validated_edges:
        incoming_by_port.setdefault((edge.target_node_id, edge.target_port), []).append(edge)

    for node in resolved_nodes.values():
        last_input_name = node.inputs[-1].name if node.inputs else None
        for input_param in node.inputs:
            incoming = incoming_by_port.get((node.node_id, input_param.name), [])
            if len(incoming) > 1 and not (node.variadic_inputs and input_param.name == last_input_name):
                errors.append(_error(f"nodes[{node.node_id}].inputs.{input_param.name}", f"Input '{input_param.name}' accepts only one incoming edge"))
            if incoming:
                continue
            if input_param.default is not None or input_param.optional:
                continue
            if node.variadic_inputs and input_param.name == last_input_name:
                continue
            if input_param.name in node.values or input_param.name in _authored_schema(node.component_cls):
                continue  # an inline literal or an authored value stands in for the wire
            errors.append(_error(f"nodes[{node.node_id}].inputs.{input_param.name}", f"Required input '{input_param.name}' is missing"))

    if errors:
        raise GraphCompilerValidationError(errors)

    return graph_id, resolved_nodes, validated_edges


def _topological_order(nodes: dict[str, ResolvedNode], edges: list[ValidatedEdge]) -> list[str]:
    indegree = {node_id: 0 for node_id in nodes}
    adjacency: dict[str, list[tuple[str, str]]] = {node_id: [] for node_id in nodes}
    for edge in edges:
        indegree[edge.target_node_id] += 1
        adjacency[edge.source_node_id].append((edge.target_node_id, edge.edge_id))

    heap: list[str] = []
    for node_id, degree in indegree.items():
        if degree == 0:
            heappush(heap, node_id)

    ordered: list[str] = []
    while heap:
        node_id = heappop(heap)
        ordered.append(node_id)
        for target_node_id, _ in sorted(adjacency[node_id], key=lambda item: (item[0], item[1])):
            indegree[target_node_id] -= 1
            if indegree[target_node_id] == 0:
                heappush(heap, target_node_id)

    if len(ordered) != len(nodes):
        raise GraphCompilerValidationError([_error("edges", "The graph contains a cycle and cannot be compiled", code="cyclic_graph")])

    return ordered


def _generic_call(ctx: EmitContext, order_index: dict[str, int]) -> str:
    """``Class(input=expr, ...)`` — wired inputs from their sources, authored ones as literals."""
    node = ctx.node
    class_name = ctx.import_component()
    authored = ctx.schema
    variadic_port = node.inputs[-1].name if node.variadic_inputs and node.inputs else None
    keyword_arguments: list[str] = []
    for input_param in node.inputs:
        connected_edges = ctx.incoming_by_port.get((node.node_id, input_param.name), [])
        if input_param.name == variadic_port:
            # Every edge on the variadic port becomes one stream, in evaluation order.
            stream_edges = sorted(connected_edges, key=lambda edge: (order_index[edge.source_node_id], edge.edge_id))
            if stream_edges:
                streams = ", ".join(
                    _source_expression(edge, ctx.port_expressions, node, input_param.name, ctx.imports) for edge in stream_edges
                )
                keyword_arguments.append(f"{input_param.name}=[{streams}]")
        elif connected_edges:
            keyword_arguments.append(f"{input_param.name}={ctx.source(input_param.name)}")
        elif input_param.name in node.values or input_param.name in authored:
            # an inline literal (or an authored value that names the input) stands in for the wire
            keyword_arguments.append(f"{input_param.name}={_literal_expression(ctx.typed(input_param.name))}")
    return f"{ctx.variable_name} = {class_name}({', '.join(keyword_arguments)})"


def compile_graph_document(document: Any) -> CompiledGraph:
    graph_id, nodes, edges = _validate_document(document)
    ordered_node_ids = _topological_order(nodes, edges)
    order_index = {node_id: index for index, node_id in enumerate(ordered_node_ids)}
    incoming_by_port: dict[tuple[str, str], list[ValidatedEdge]] = {}
    for edge in edges:
        incoming_by_port.setdefault((edge.target_node_id, edge.target_port), []).append(edge)

    imports: set[tuple[str, str]] = set()
    variable_names: dict[str, str] = {}
    # (node id, output port) -> expression yielding that output (after any output port op)
    port_expressions: dict[tuple[str, str], str] = {}
    result_expressions: dict[str, str] = {}
    lines: list[str] = []

    for index, node_id in enumerate(ordered_node_ids):
        node = nodes[node_id]
        node_name = _component_name(node.component_cls)
        variable_name = f"node_{index:03d}_{_snake_case(node_name)}"
        variable_names[node_id] = variable_name

        if node.component_cls is None:
            # Object references bake the scene atom and its placement into the source.
            imports.add(("pyhopper.Core.DataTree", "DataTree"))
            imports.add(("pyhopper.Core.Atoms", "AtomicTransform"))
            imports.add(("pyhopper.Core.Atoms", "atom_from_json"))
            imports.add(("pyhopper.Utils.Transforms", "apply_transform"))
            lines.append(
                f"{variable_name} = DataTree.from_item(apply_transform("
                f"AtomicTransform.from_json({node.object_transform!r}), "
                f"atom_from_json({node.object_atom!r})))"
            )
        else:
            context = EmitContext(node, variable_name, imports, incoming_by_port, port_expressions)
            emitter = AUTHORED_EMITTERS.get(getattr(node.component_cls, "authored_emit", None) or "")
            line = emitter(context) if emitter else None
            lines.append(line if line is not None else _generic_call(context, order_index))

        # Register how downstream nodes read each output. Output port operations get their
        # own variable so the node result (and its sibling outputs) is never rebound.
        primary_name = node.outputs[0].name if node.outputs else ""
        result_expressions[node_id] = variable_name
        for output in node.outputs:
            base_expr = _output_expression(variable_name, output.name, primary_name)
            op_name = node.port_operations.get(f"output:{output.name}")
            if op_name:
                op_variable = f"{variable_name}__{_snake_case(output.name)}"
                lines.append(f"{op_variable} = {_apply_port_operation(base_expr, op_name, imports)}")
                port_expressions[(node_id, output.name)] = op_variable
                if output.name == primary_name:
                    result_expressions[node_id] = op_variable
            else:
                port_expressions[(node_id, output.name)] = base_expr

    preview_node_ids = [node_id for node_id in ordered_node_ids if nodes[node_id].preview_enabled]
    if not preview_node_ids:
        raise GraphCompilerValidationError([_error("nodes", "Graph does not contain any preview-enabled nodes", code="missing_output")])

    merge_module, _, merge_class = MERGE_COMPONENT_KEY.rpartition(".")
    if len(preview_node_ids) > 1:
        imports.add((merge_module, merge_class))

    import_lines = [f"from {module_name} import {class_name}" for module_name, class_name in sorted(imports)]
    source_lines = [
        "from __future__ import annotations",
        "",
        *import_lines,
        "",
        f"def {NODE_OUTPUTS_ENTRYPOINT}():",
        *[f"    {line}" for line in lines],
        "    return {",
        *[f"        {node_id!r}: {result_expressions[node_id]}," for node_id in ordered_node_ids],
        "    }",
        "",
        f"def {PREVIEW_OUTPUTS_ENTRYPOINT}():",
        f"    node_outputs = {NODE_OUTPUTS_ENTRYPOINT}()",
        "    return {",
        *[f"        {node_id!r}: node_outputs[{node_id!r}]," for node_id in preview_node_ids],
        "    }",
        "",
        f"def {ENTRYPOINT_NAME}():",
        f"    preview_outputs = {PREVIEW_OUTPUTS_ENTRYPOINT}()",
        "    preview_values = list(preview_outputs.values())",
        "    if len(preview_values) == 1:",
        "        return preview_values[0]",
        f"    return {merge_class}(*preview_values)",
        "",
    ]
    return CompiledGraph(graph_id=graph_id, source="\n".join(source_lines), preview_node_ids=tuple(preview_node_ids))


def execute_compiled_graph(compiled_graph: CompiledGraph, output_dir: str | Path) -> dict[str, Any]:
    namespace: dict[str, Any] = {}
    exec(compiled_graph.source, namespace, namespace)
    node_outputs = namespace[compiled_graph.node_outputs_entrypoint]()
    if not isinstance(node_outputs, dict) or not node_outputs:
        raise RuntimeError("Compiled graph did not produce any node outputs")

    preview_outputs = {node_id: node_outputs[node_id] for node_id in compiled_graph.preview_node_ids if node_id in node_outputs}
    if not preview_outputs:
        raise RuntimeError("Compiled graph did not produce any preview outputs")

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{_sanitize_filename(compiled_graph.graph_id)}.glb"
    render_manifest = export_glb_with_manifest(preview_outputs, output_path)

    return {
        "compiled_graph": compiled_graph,
        "output_path": output_path,
        "node_outputs": node_outputs,
        "node_previews": {node_id: serialize_preview_value(value) for node_id, value in node_outputs.items()},
        "render_manifest": render_manifest,
    }
