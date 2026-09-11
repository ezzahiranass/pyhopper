"""Lock the compiler's generated source for authored nodes.

The special input nodes (sliders, toggle, panel, graph mapper, point on
curve, object references) bake their authored values into the emitted
Python. This fixture covers every emitter so a refactor of the compiler
must reproduce the source byte for byte; record a new golden with
``PYHOPPER_UPDATE_GOLDEN=1`` only when the emitted code changes on purpose.
"""

from __future__ import annotations

import unittest

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint, AtomicTransform
from pyhopper.Graph.runtime import compile_graph_document
from tests.support.golden import UPDATE, golden_path, read_text, write_text

BOOLEAN_TOGGLE = "pyhopper.Components.Params.Input.BooleanToggle.BooleanToggle"
MD_SLIDER = "pyhopper.Components.Params.Input.MDSlider.MDSlider"
NUMBER_SLIDER = "pyhopper.Components.Params.Input.NumberSlider.NumberSlider"
GRAPH_MAPPER = "pyhopper.Components.Params.Input.GraphMapper.GraphMapper"
PANEL = "pyhopper.Components.Params.Input.Panel.Panel"
POINT_ON_CURVE = "pyhopper.Components.Curve.Analysis.PointOnCurve.PointOnCurve"
SERIES = "pyhopper.Components.Maths.Series.Series"
DIVIDE_CURVE = "pyhopper.Components.Curve.Division.DivideCurve.DivideCurve"


def node(node_id: str, key: str, *, preview: bool = True, settings=None, values=None, port_operations=None) -> dict:
    tab, category, name = key.split(".")[2], key.split(".")[3], key.split(".")[-1]
    return {
        "id": node_id,
        "kind": "component",
        "componentKey": key,
        "component": {"tab": tab, "category": category, "name": name},
        "position": {"x": 0.0, "y": 0.0},
        "previewEnabled": preview,
        "settings": settings or {},
        "values": values or {},
        "portOperations": port_operations or {},
    }


def edge(edge_id: str, source: str, source_port: str, target: str, target_port: str) -> dict:
    return {"id": edge_id, "sourceNodeId": source, "sourcePort": source_port, "targetNodeId": target, "targetPort": target_port}


def authored_document() -> dict:
    line = AtomicLine(AtomicPoint(0.0, 0.0, 0.0), AtomicPoint(8.0, 0.0, 0.0))
    return {
        "schemaVersion": 2,
        "graphId": "authored-nodes",
        "viewport": {"x": 0.0, "y": 0.0, "zoom": 1.0},
        "scene": {
            "schemaVersion": 3,
            "objects": {
                "line": {
                    "id": "line",
                    "name": "Line",
                    "atom": line.to_json(),
                    "transform": AtomicTransform.identity().to_json(),
                },
            },
        },
        "nodes": [
            node("toggle", BOOLEAN_TOGGLE, values={"value": True}),
            node("toggle-default", BOOLEAN_TOGGLE),
            node("md", MD_SLIDER, values={"x": 0.2, "y": 0.8}),
            node("slider", NUMBER_SLIDER, settings={"value": 4.74, "min": 0.0, "max": 10.0, "decimals": 2, "rounding": "integer"}),
            node("slider-legacy", NUMBER_SLIDER, values={"value": 0.25}),
            node("slider-plain", NUMBER_SLIDER),
            node("mapper", GRAPH_MAPPER, values={"graphType": "linear", "xMin": 0, "xMax": 1, "yMin": 10, "yMax": 20}),
            node("panel", PANEL, values={"text": "12\nfixed value", "textAlign": "center"}),
            node("viewer", PANEL, values={"text": "ignored while connected"}),
            node("integer-panel", PANEL, values={"text": "25"}),
            node("multiline-panel", PANEL, values={"text": "25\n16\ntrue\nlabel", "multilineData": True}),
            node("curve-point", POINT_ON_CURVE, values={"parameter": 0.25}),
            node("curve-point-default", POINT_ON_CURVE),
            node("series", SERIES, port_operations={"output:series": "Graft"}),
            node("divide", DIVIDE_CURVE, port_operations={"input:curve": "Reparametrize"}),
            {
                "id": "line-reference",
                "kind": "object-reference",
                "objectId": "line",
                "position": {"x": 0.0, "y": 0.0},
                "previewEnabled": True,
                "values": {},
                "portOperations": {},
            },
        ],
        "edges": [
            edge("slider-mapper", "slider", "value", "mapper", "numbers"),
            edge("mapper-viewer", "mapper", "mapped", "viewer", "data"),
            edge("line-curve-point", "line-reference", "geometry", "curve-point", "curve"),
            edge("line-curve-point-default", "line-reference", "geometry", "curve-point-default", "curve"),
            edge("line-divide", "line-reference", "geometry", "divide", "curve"),
            edge("slider-divide", "slider", "value", "divide", "count"),
        ],
    }


class CompiledSourceGoldenTests(unittest.TestCase):
    def test_authored_nodes_source_matches_golden(self):
        compiled = compile_graph_document(authored_document())
        path = golden_path("compiled", "authored_nodes.py")
        if UPDATE or not path.exists():
            write_text(path, compiled.source)
        self.assertEqual(compiled.source.strip(), read_text(path))

    def test_authored_nodes_source_executes(self):
        compiled = compile_graph_document(authored_document())
        namespace: dict = {}
        exec(compiled.source, namespace, namespace)
        outputs = namespace[compiled.node_outputs_entrypoint]()
        self.assertEqual(outputs["toggle"].all_items(), [True])
        self.assertEqual(outputs["toggle-default"].all_items(), [False])
        self.assertEqual(outputs["slider"].all_items(), [5.0])
        self.assertEqual(outputs["slider-legacy"].all_items(), [0.25])
        self.assertEqual(outputs["slider-plain"].all_items(), [0.5])
        self.assertEqual(outputs["mapper"].all_items(), [20.0])
        self.assertEqual(outputs["integer-panel"].all_items(), [25])
        self.assertEqual(outputs["multiline-panel"].all_items(), [25, 16, True, "label"])
        self.assertEqual(outputs["curve-point"].all_items(), [AtomicPoint(2.0, 0.0, 0.0)])
        self.assertEqual(outputs["curve-point-default"].all_items(), [AtomicPoint(4.0, 0.0, 0.0)])
        self.assertEqual(len(outputs["divide"]), 6)


if __name__ == "__main__":
    unittest.main()
