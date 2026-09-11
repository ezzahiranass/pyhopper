"""Declarative authored values: schema validation, the emitter registry and the hook."""

from __future__ import annotations

import unittest

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Graph.catalog import serialize_component
from pyhopper.Graph.runtime import GraphCompilerValidationError, compile_graph_document

BOOLEAN_TOGGLE = "pyhopper.Components.Params.Input.BooleanToggle.BooleanToggle"
GRAPH_MAPPER = "pyhopper.Components.Params.Input.GraphMapper.GraphMapper"
NUMBER_SLIDER = "pyhopper.Components.Params.Input.NumberSlider.NumberSlider"
PANEL = "pyhopper.Components.Params.Input.Panel.Panel"
POINT_ON_CURVE = "pyhopper.Components.Curve.Analysis.PointOnCurve.PointOnCurve"
SERIES = "pyhopper.Components.Maths.Series.Series"


class Gate(Component):
    """Test double: an authored threshold with a cross-field rule (``low`` below ``high``)."""

    inputs = [InputParam("value", float, Access.ITEM, default=0.0)]
    outputs = [OutputParam("inside", bool)]
    authored_values = {
        "low": {"type": "float", "default": 0.0},
        "high": {"type": "float", "default": 1.0},
        "mode": {"type": "choice", "default": "closed", "choices": ["closed", "open"]},
    }

    @classmethod
    def validate_authored(cls, section, data):
        if section == "values" and data.get("low", 0.0) > data.get("high", 1.0):
            return [("low", "low must not exceed high")]
        return []

    def generate(self, value=0.0):
        return 0.0 <= value <= 1.0


class Stamp(Component):
    """Test double: declares an emitter the compiler does not know."""

    outputs = [OutputParam("stamp", str)]
    authored_values = {"text": {"type": "string", "default": ""}}
    authored_emit = "hologram"

    def generate(self):
        return ""


GATE = f"{__name__}.Gate"
STAMP = f"{__name__}.Stamp"
LINE_OBJECT = {
    "id": "line",
    "name": "Line",
    "atom": {
        "type": "Line",
        "start": {"type": "Point3d", "x": 0.0, "y": 0.0, "z": 0.0},
        "end": {"type": "Point3d", "x": 4.0, "y": 0.0, "z": 0.0},
    },
    "transform": {"type": "Transform", "matrix": [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]},
}


def node(node_id: str, key: str, *, settings=None, values=None) -> dict:
    parts = key.split(".")
    tab, category = (parts[2], parts[3]) if len(parts) > 4 else ("Test", "Test")
    return {
        "id": node_id,
        "kind": "component",
        "componentKey": key,
        "component": {"tab": tab, "category": category, "name": parts[-1]},
        "position": {"x": 0.0, "y": 0.0},
        "previewEnabled": True,
        "settings": settings or {},
        "values": values or {},
        "portOperations": {},
    }


def reference(node_id: str, object_id: str) -> dict:
    return {
        "id": node_id,
        "kind": "object-reference",
        "objectId": object_id,
        "position": {"x": 0.0, "y": 0.0},
        "previewEnabled": True,
        "values": {},
        "portOperations": {},
    }


def edge(edge_id: str, source: str, source_port: str, target: str, target_port: str) -> dict:
    return {"id": edge_id, "sourceNodeId": source, "sourcePort": source_port, "targetNodeId": target, "targetPort": target_port}


def document(nodes: list[dict], edges: list[dict] | None = None, objects: dict | None = None) -> dict:
    return {
        "schemaVersion": 2,
        "graphId": "authored-values",
        "scene": {"schemaVersion": 3, "objects": objects or {}},
        "viewport": {"x": 0.0, "y": 0.0, "zoom": 1.0},
        "nodes": nodes,
        "edges": edges or [],
    }


def errors_of(doc: dict) -> list[tuple[str, str]]:
    try:
        compile_graph_document(doc)
    except GraphCompilerValidationError as exc:
        return [(error["path"], error["message"]) for error in exc.errors]
    return []


class AuthoredValidationTests(unittest.TestCase):
    def test_declared_values_type_check(self):
        errors = errors_of(document([node("t", BOOLEAN_TOGGLE, values={"value": 1})]))
        self.assertEqual(errors, [("nodes[0].values.value", "'value' must be boolean")])

    def test_unknown_authored_value_is_rejected(self):
        errors = errors_of(document([node("t", BOOLEAN_TOGGLE, values={"value": True, "colour": "red"})]))
        self.assertEqual(errors, [("nodes[0].values.colour", "Unknown authored value 'colour'")])

    def test_choice_values_must_be_one_of_the_choices(self):
        errors = errors_of(document([node("p", PANEL, values={"textAlign": "justify"})]))
        self.assertEqual(errors, [("nodes[0].values.textAlign", "Unsupported textAlign 'justify'")])

    def test_components_without_authored_values_reject_values(self):
        errors = errors_of(document([node("s", SERIES, values={"count": 5})]))
        self.assertEqual(errors, [("nodes[0].values.count", "Series does not declare authored values")])

    def test_settings_emitter_validates_settings_strictly(self):
        errors = errors_of(document([node("s", NUMBER_SLIDER, settings={"value": 0.5, "rounding": "banker", "colour": "red"})]))
        self.assertEqual(
            errors,
            [
                ("nodes[0].settings.rounding", "Unsupported rounding 'banker'"),
                ("nodes[0].settings.colour", "Unknown setting 'colour'"),
            ],
        )

    def test_settings_emitter_accepts_the_legacy_value_under_the_output_name(self):
        self.assertEqual(errors_of(document([node("s", NUMBER_SLIDER, values={"value": 0.25})])), [])
        errors = errors_of(document([node("s", NUMBER_SLIDER, values={"min": 0.0})]))
        self.assertEqual(errors, [("nodes[0].values.min", "NumberSlider stores authored values in settings")])

    def test_unread_settings_are_ignored_but_declared_ones_type_check(self):
        # a stale settings key from an older catalog must not break a saved graph
        self.assertEqual(errors_of(document([node("t", BOOLEAN_TOGGLE, settings={"value": False})])), [])
        self.assertEqual(errors_of(document([node("g", GATE, settings={"anything": 1})])), [])
        md_slider = "pyhopper.Components.Params.Input.MDSlider.MDSlider"
        errors = errors_of(document([node("m", md_slider, settings={"x_min": "zero"})]))
        self.assertEqual(errors, [("nodes[0].settings.x_min", "'x_min' must be numeric")])

    def test_validate_authored_hook_runs_after_schema_checks(self):
        errors = errors_of(document([node("g", GATE, values={"low": 2.0, "high": 1.0})]))
        self.assertEqual(errors, [("nodes[0].values.low", "low must not exceed high")])
        # a schema failure short-circuits the hook so it never sees malformed data
        errors = errors_of(document([node("g", GATE, values={"low": "2", "high": 1.0})]))
        self.assertEqual(errors, [("nodes[0].values.low", "'low' must be numeric")])

    def test_unknown_emitter_is_a_validation_error(self):
        errors = errors_of(document([node("s", STAMP)]))
        self.assertEqual(errors, [("nodes[0].componentKey", "Stamp declares unknown authored_emit 'hologram'")])


class AuthoredEmissionTests(unittest.TestCase):
    def test_only_authored_values_naming_an_input_become_literals(self):
        compiled = compile_graph_document(document([node("g", GATE, values={"low": 0.25})]))
        self.assertIn("node_000_gate = Gate()", compiled.source)  # `low` is authored data, not an input

    def test_authored_input_literal_uses_the_value_or_its_default(self):
        doc = document(
            [node("p", POINT_ON_CURVE, values={"parameter": 0.75}), node("q", POINT_ON_CURVE), reference("line", "line")],
            [edge("e1", "line", "geometry", "p", "curve"), edge("e2", "line", "geometry", "q", "curve")],
            {"line": LINE_OBJECT},
        )
        source = compile_graph_document(doc).source
        self.assertIn("parameter=0.75)", source)
        self.assertIn("parameter=0.5)", source)

    def test_a_wire_wins_over_the_authored_input_literal(self):
        doc = document(
            [node("p", POINT_ON_CURVE, values={"parameter": 0.75}), node("s", NUMBER_SLIDER, settings={"value": 0.1}), reference("line", "line")],
            [edge("e1", "line", "geometry", "p", "curve"), edge("e2", "s", "value", "p", "parameter")],
            {"line": LINE_OBJECT},
        )
        source = compile_graph_document(doc).source
        self.assertNotIn("parameter=0.75", source)
        self.assertIn("parameter=node_", source)

    def test_graph_mapper_needs_its_wire(self):
        errors = errors_of(document([node("m", GRAPH_MAPPER, values={"graphType": "sine"})]))
        self.assertEqual([message for _, message in errors], ["Required input 'numbers' is missing"])

    def test_catalog_serialises_the_declarations(self):
        entry = serialize_component("Test", "Test", Gate)
        self.assertIsNone(entry["authored_emit"])
        self.assertEqual(entry["initial_values"], {"low": 0.0, "high": 1.0, "mode": "closed"})
        self.assertEqual(entry["authored_values"]["mode"]["choices"], ["closed", "open"])
        self.assertEqual(Gate.authored_defaults(), {"low": 0.0, "high": 1.0, "mode": "closed"})


if __name__ == "__main__":
    unittest.main()
