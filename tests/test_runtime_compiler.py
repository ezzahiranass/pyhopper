"""Graph compiler behaviour: variadic streams, port operations, preview entrypoint."""

from __future__ import annotations

import unittest

from pyhopper.Graph.runtime import compile_graph_document

SERIES = "pyhopper.Components.Maths.Series.Series"
MERGE = "pyhopper.Components.Sets.Tree.Merge.Merge"
POLYLINE = "pyhopper.Components.Curve.Spline.Polyline.Polyline"
INTERPOLATE = "pyhopper.Components.Curve.Spline.Interpolate.Interpolate"
LENGTH = "pyhopper.Components.Curve.Analysis.Length.Length"
CONSTRUCT_POINT = "pyhopper.Components.Vector.Point.ConstructPoint.ConstructPoint"
NUMBER_SLIDER = "pyhopper.Components.Params.Input.NumberSlider.NumberSlider"


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


def document(nodes: list[dict], edges: list[dict]) -> dict:
    return {
        "schemaVersion": 2,
        "graphId": "compiler-test",
        "scene": {"schemaVersion": 3, "objects": {}},
        "viewport": {"x": 0.0, "y": 0.0, "zoom": 1.0},
        "nodes": nodes,
        "edges": edges,
    }


def run(doc: dict):
    compiled = compile_graph_document(doc)
    namespace: dict = {}
    exec(compiled.source, namespace, namespace)
    return compiled, namespace[compiled.node_outputs_entrypoint](), namespace


class VariadicCompileTests(unittest.TestCase):
    def test_variadic_component_receives_every_edge_as_a_keyword_stream_list(self):
        doc = document(
            [
                node("a", SERIES, preview=False),
                node("b", SERIES, preview=False, settings={}, values={}),
                node("m", MERGE),
            ],
            [edge("e1", "a", "series", "m", "data"), edge("e2", "b", "series", "m", "data")],
        )
        compiled, outputs, _ = run(doc)
        self.assertIn("Merge(data=[node_000_series, node_001_series])", compiled.source)
        self.assertEqual(outputs["m"].all_items(), list(range(10)) + list(range(10)))

    def test_variadic_component_without_edges_compiles_to_bare_call(self):
        compiled, outputs, _ = run(document([node("m", MERGE)], []))
        self.assertIn("node_000_merge = Merge()", compiled.source)
        self.assertEqual(outputs["m"].branch_count, 0)

    def test_preview_entrypoint_merges_positionally(self):
        doc = document([node("a", SERIES), node("b", SERIES)], [])
        compiled, _, namespace = run(doc)
        self.assertIn("return Merge(*preview_values)", compiled.source)
        merged = namespace[compiled.entrypoint]()
        self.assertEqual(len(merged.all_items()), 20)


class PortOperationCompileTests(unittest.TestCase):
    def test_interpolate_needs_two_points_so_use_series_driven_points(self):
        # Sanity: the shared fixture must be executable before we test port ops on it.
        doc = document(
            [
                node("s", SERIES, preview=False),
                node("p", CONSTRUCT_POINT, preview=False),
                node("pl", INTERPOLATE),
                node("len", LENGTH),
            ],
            [
                edge("e0", "s", "series", "p", "x_coordinate"),
                edge("e1", "p", "point", "pl", "vertices"),
                edge("e2", "pl", "curve", "len", "curve"),
            ],
        )
        _, outputs, _ = run(doc)
        self.assertAlmostEqual(outputs["len"].all_items()[0], 9.0, places=6)

    def test_output_port_operation_on_secondary_output_does_not_rebind_node_variable(self):
        doc = document(
            [
                node("s", SERIES, preview=False),
                node("p", CONSTRUCT_POINT, preview=False),
                node("pl", INTERPOLATE, port_operations={"output:length": "Graft"}),
                node("len", LENGTH),
            ],
            [
                edge("e0", "s", "series", "p", "x_coordinate"),
                edge("e1", "p", "point", "pl", "vertices"),
                edge("e2", "pl", "curve", "len", "curve"),
            ],
        )
        compiled, outputs, _ = run(doc)
        self.assertIn("node_002_interpolate__length = node_002_interpolate.length.graft()", compiled.source)
        self.assertNotIn("node_002_interpolate = node_002_interpolate", compiled.source)
        self.assertAlmostEqual(outputs["len"].all_items()[0], 9.0, places=6)
        self.assertEqual(outputs["pl"].output_names, ["curve", "length", "domain"])

    def test_output_port_operation_on_primary_output_feeds_downstream_and_previews(self):
        doc = document(
            [node("s", SERIES, port_operations={"output:series": "Graft"}), node("m", MERGE)],
            [edge("e1", "s", "series", "m", "data")],
        )
        compiled, outputs, _ = run(doc)
        self.assertIn("node_000_series__series = node_000_series.graft()", compiled.source)
        self.assertEqual(outputs["s"].branch_count, 10)
        self.assertEqual(outputs["m"].branch_count, 10)

    def test_input_port_operation_is_applied_to_the_source_expression(self):
        doc = document(
            [node("s", SERIES, preview=False), node("m", MERGE, port_operations={"input:data": "Graft"})],
            [edge("e1", "s", "series", "m", "data")],
        )
        compiled, outputs, _ = run(doc)
        self.assertIn("Merge(data=[node_000_series.graft()])", compiled.source)
        self.assertEqual(outputs["m"].branch_count, 10)


if __name__ == "__main__":
    unittest.main()
