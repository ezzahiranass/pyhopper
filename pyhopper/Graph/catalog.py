from __future__ import annotations

from inspect import getdoc
from typing import Any

from pyhopper.Core.Component import Component, InputParam, OutputParam
from pyhopper.Core.Path import Path
from pyhopper.Core.TypeSystem import accepted_type_names, type_name



def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)  # "{0;1}" — the spelling Panels and text ports use for paths
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    to_json = getattr(value, "to_json", None)
    if callable(to_json):
        try:
            return _json_safe(to_json())
        except Exception:
            pass

    return repr(value)


# Inline literals: a node may carry ``values[<input>]`` for any primitive-typed input that
# is not the variadic port (Grasshopper's "Set Data Item" on an unwired input).
LITERAL_INPUT_TYPES: dict[type, str] = {float: "float", int: "int", bool: "bool", str: "string"}


def literal_input_names(component_cls: type[Component] | None) -> dict[str, dict[str, Any]]:
    """Inputs that accept an inline literal, as ``{name: {"type": schema type}}`` specs."""
    if component_cls is None:
        return {}
    inputs = list(getattr(component_cls, "inputs", []))
    variadic = inputs[-1].name if getattr(component_cls, "variadic_inputs", False) and inputs else None
    return {
        param.name: {"type": LITERAL_INPUT_TYPES[param.type_hint]}
        for param in inputs
        if param.type_hint in LITERAL_INPUT_TYPES and param.name != variadic
    }


def serialize_input(param: InputParam, *, literal: bool = False) -> dict[str, Any]:
    return {
        "name": param.name,
        "type": type_name(param.type_hint),
        "accepts": accepted_type_names(param.type_hint),
        "access": param.access.value,
        "default": _json_safe(param.default),
        "optional": param.optional,
        "literal": literal,
    }


def serialize_output(param: OutputParam) -> dict[str, Any]:
    return {
        "name": param.name,
        "type": type_name(param.type_hint),
        "access": param.access.value,
    }


def _schema(component_cls: type[Component], attribute: str) -> dict[str, Any]:
    schema = getattr(component_cls, attribute, None)
    return schema if isinstance(schema, dict) else {}


def _schema_defaults(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        key: _json_safe(spec.get("default"))
        for key, spec in schema.items()
        if isinstance(spec, dict) and "default" in spec
    }


def serialize_component(tab: str, category: str, component_cls: type[Component]) -> dict[str, Any]:
    literal_inputs = literal_input_names(component_cls)
    inputs = [serialize_input(param, literal=param.name in literal_inputs) for param in getattr(component_cls, "inputs", [])]
    outputs = [serialize_output(param) for param in getattr(component_cls, "outputs", [])]
    settings_schema = _schema(component_cls, "settings_schema")
    authored_values = _schema(component_cls, "authored_values")
    variadic_inputs = bool(getattr(component_cls, "variadic_inputs", False))
    settings_defaults = _schema_defaults(settings_schema)

    return {
        "component_key": f"{component_cls.__module__}.{component_cls.__name__}",
        "module": component_cls.__module__,
        "tab": tab,
        "category": category,
        "component": component_cls.__name__,
        "display_name": getattr(component_cls, "display_name", None) or component_cls.__name__,
        "nickname": getattr(component_cls, "nickname", None) or component_cls.__name__,
        "gh_guid": getattr(component_cls, "gh_guid", None),
        "description": getdoc(component_cls) or "",
        "settings_schema": _json_safe(settings_schema),
        "settings_defaults": settings_defaults,
        "initial_settings": dict(settings_defaults),
        "authored_values": _json_safe(authored_values),
        "authored_emit": getattr(component_cls, "authored_emit", None),
        "initial_values": _schema_defaults(authored_values),
        "input_count": len(inputs),
        "output_count": len(outputs),
        "variadic_inputs": variadic_inputs,
        "inputs": inputs,
        "outputs": outputs,
    }


def list_components() -> list[dict[str, Any]]:
    from pyhopper.Components.registry import iter_component_classes

    components = [serialize_component(entry.tab, entry.category, entry.cls) for entry in iter_component_classes()]
    components.sort(key=lambda item: (item["tab"], item["category"], item["component"]))
    return components
