"""Catalog smoke test: every component under pyhopper/Components must be well-formed.

Checks, per component: it serialises for the web catalog, module and class
docstrings exist (mkdocs --strict renders them), port names are identifiers,
output names do not collide with DataTree/ComponentResult attributes,
``generate`` accepts every declared input, and — when every required input
has a default — a one-node graph compiles and executes through the runtime.
"""

from __future__ import annotations

import inspect
import json
import sys
import unittest
from importlib import import_module

from pyhopper.Core.Component import Access, Component, ComponentResult, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Graph.catalog import list_components
from pyhopper.Graph.runtime import (
    AUTHORED_EMITTERS,
    SCHEMA_TYPE_CHECKS,
    GraphCompilerValidationError,
    compile_graph_document,
)

RESERVED_OUTPUT_NAMES = {name for name in set(dir(DataTree)) | set(dir(ComponentResult)) if not name.startswith("_")}


def _resolve(component_key: str) -> type[Component]:
    module_name, _, class_name = component_key.rpartition(".")
    return getattr(import_module(module_name), class_name)


def _single_node_document(entry: dict) -> dict:
    return {
        "schemaVersion": 2,
        "graphId": f"smoke-{entry['component']}",
        "scene": {"schemaVersion": 3, "objects": {}},
        "viewport": {"x": 0.0, "y": 0.0, "zoom": 1.0},
        "nodes": [
            {
                "id": "node",
                "kind": "component",
                "componentKey": entry["component_key"],
                "component": {"tab": entry["tab"], "category": entry["category"], "name": entry["component"]},
                "position": {"x": 0.0, "y": 0.0},
                "previewEnabled": True,
                "settings": {},
                "values": {},
                "portOperations": {},
            }
        ],
        "edges": [],
    }


def _has_all_defaults(component_cls: type[Component]) -> bool:
    inputs: list[InputParam] = list(getattr(component_cls, "inputs", []))
    variadic = bool(getattr(component_cls, "variadic_inputs", False))
    for index, param in enumerate(inputs):
        if param.default is not None or param.optional:
            continue
        if variadic and index == len(inputs) - 1:
            continue
        return False
    return True


class CatalogSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entries = list_components()
        cls.classes = {entry["component_key"]: _resolve(entry["component_key"]) for entry in cls.entries}

    def test_catalog_is_not_empty_and_json_serialisable(self) -> None:
        self.assertGreaterEqual(len(self.entries), 117)
        json.dumps(self.entries)
        keys = [entry["component_key"] for entry in self.entries]
        self.assertEqual(len(keys), len(set(keys)), "duplicate component keys in catalog")

    def test_every_component_has_docstrings(self) -> None:
        for key, component_cls in self.classes.items():
            with self.subTest(component=key):
                module = sys.modules[component_cls.__module__]
                self.assertTrue((module.__doc__ or "").strip(), "module docstring missing")
                self.assertTrue((component_cls.__doc__ or "").strip(), "class docstring missing")

    def test_port_declarations_are_well_formed(self) -> None:
        for key, component_cls in self.classes.items():
            with self.subTest(component=key):
                inputs: list[InputParam] = list(getattr(component_cls, "inputs", []))
                outputs: list[OutputParam] = list(getattr(component_cls, "outputs", []))
                input_names = [param.name for param in inputs]
                output_names = [param.name for param in outputs]
                self.assertTrue(outputs, "component declares no outputs")
                self.assertEqual(len(input_names), len(set(input_names)), "duplicate input names")
                self.assertEqual(len(output_names), len(set(output_names)), "duplicate output names")
                for name in input_names + output_names:
                    self.assertTrue(name.isidentifier(), f"port name {name!r} is not an identifier")
                for name in output_names:
                    self.assertNotIn(name, RESERVED_OUTPUT_NAMES, f"output {name!r} shadows a DataTree attribute")
                    self.assertFalse(name.startswith("_"), f"output {name!r} must not start with '_'")
                for param in inputs:
                    self.assertIsInstance(param.access, Access)
                if getattr(component_cls, "variadic_inputs", False):
                    self.assertTrue(inputs, "variadic component must declare at least one input")

    def test_authored_declarations_are_well_formed(self) -> None:
        """settings_schema / authored_values specs use the shared type vocabulary and sane defaults."""
        primitive_types = {float, int, bool, str}
        for key, component_cls in self.classes.items():
            with self.subTest(component=key):
                emit = getattr(component_cls, "authored_emit", None)
                self.assertTrue(emit is None or emit in AUTHORED_EMITTERS, f"unknown authored_emit {emit!r}")
                input_types = {param.name: param.type_hint for param in getattr(component_cls, "inputs", [])}
                for attribute in ("settings_schema", "authored_values"):
                    schema = getattr(component_cls, attribute, {})
                    self.assertIsInstance(schema, dict)
                    for name, spec in schema.items():
                        self.assertTrue(name.isidentifier(), f"{attribute} key {name!r} is not an identifier")
                        self.assertIsInstance(spec, dict, f"{attribute}[{name!r}] is not a spec dict")
                        kind = spec.get("type")
                        self.assertIn(kind, SCHEMA_TYPE_CHECKS, f"{attribute}[{name!r}] has unknown type {kind!r}")
                        self.assertIn("default", spec, f"{attribute}[{name!r}] declares no default")
                        self.assertTrue(SCHEMA_TYPE_CHECKS[kind](spec["default"]), f"{attribute}[{name!r}] default fails its own type")
                        if kind == "choice":
                            self.assertIn(spec["default"], spec.get("choices", ()), f"{attribute}[{name!r}] default is not a choice")
                        for bound in ("min", "max"):
                            if bound in spec:
                                self.assertIn(kind, {"float", "int"}, f"{attribute}[{name!r}] bounds need a numeric type")
                # authored values that name an input become literals: the input must be primitive
                for name in getattr(component_cls, "authored_values", {}):
                    if name in input_types:
                        self.assertIn(input_types[name], primitive_types, f"authored input {name!r} must be float/int/bool/str typed")
                if emit == "settings":
                    self.assertTrue(getattr(component_cls, "settings_schema", {}), "settings emitter needs a settings_schema")
                elif emit is not None:
                    self.assertTrue(getattr(component_cls, "authored_values", {}), f"{emit!r} emitter needs authored_values")

    def test_catalog_exposes_authored_declarations(self) -> None:
        by_name = {entry["component"]: entry for entry in self.entries}
        toggle = by_name["BooleanToggle"]
        self.assertEqual(toggle["authored_emit"], "literal")
        self.assertEqual(toggle["initial_values"], {"value": False})
        self.assertEqual(toggle["initial_settings"], {})
        self.assertEqual(toggle["authored_values"]["value"]["type"], "bool")
        mapper = by_name["GraphMapper"]
        self.assertEqual(mapper["authored_emit"], "graph_mapper")
        self.assertEqual(mapper["initial_settings"], {})
        self.assertEqual(mapper["initial_values"]["graphType"], "bezier")
        self.assertEqual(mapper["authored_values"]["graphType"]["choices"], ["bezier", "gaussian", "linear", "sine"])
        panel = by_name["Panel"]
        self.assertEqual(panel["initial_values"], {"text": "", "textAlign": "left", "multilineData": False})
        md_slider = by_name["MDSlider"]
        self.assertEqual(md_slider["initial_values"], {"x": 0.5, "y": 0.5})
        self.assertEqual(set(md_slider["initial_settings"]), {"x_min", "x_max", "y_min", "y_max", "decimals"})
        slider = by_name["NumberSlider"]
        self.assertEqual(slider["authored_emit"], "settings")
        self.assertEqual(slider["initial_values"], {})
        self.assertEqual(slider["initial_settings"]["rounding"], "real")
        point = by_name["PointOnCurve"]
        self.assertIsNone(point["authored_emit"])
        self.assertEqual(point["initial_values"], {"parameter": 0.5})
        series = by_name["Series"]
        self.assertEqual((series["authored_values"], series["authored_emit"], series["initial_values"]), ({}, None, {}))

    def test_generate_accepts_every_declared_input(self) -> None:
        for key, component_cls in self.classes.items():
            with self.subTest(component=key):
                signature = inspect.signature(component_cls.generate)
                accepts_kwargs = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in signature.parameters.values())
                if accepts_kwargs:
                    continue
                for param in getattr(component_cls, "inputs", []):
                    self.assertIn(param.name, signature.parameters, f"generate() has no parameter for input {param.name!r}")

    def test_default_only_components_compile_and_execute(self) -> None:
        compiled = 0
        skipped: list[str] = []
        for entry in self.entries:
            component_cls = self.classes[entry["component_key"]]
            if not _has_all_defaults(component_cls):
                skipped.append(entry["component"])
                continue
            with self.subTest(component=entry["component_key"]):
                try:
                    graph = compile_graph_document(_single_node_document(entry))
                except GraphCompilerValidationError as exc:
                    self.fail(f"validation failed: {exc.errors}")
                namespace: dict = {}
                exec(graph.source, namespace, namespace)
                outputs = namespace[graph.node_outputs_entrypoint]()
                self.assertIn("node", outputs)
                compiled += 1
        self.assertGreater(compiled, 0)
        # Components with required inputs cannot be exercised without wiring; keep the count visible.
        self.assertLess(len(skipped), len(self.entries))


if __name__ == "__main__":
    unittest.main()
