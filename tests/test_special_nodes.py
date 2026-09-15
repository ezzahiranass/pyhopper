from __future__ import annotations

import unittest

from pyhopper.Graph.runtime import compile_graph_document
from pyhopper import AtomicLine, AtomicPoint, AtomicTransform, BooleanToggle, GraphMapper, MDSlider, NumberSlider, PointOnCurve
from pyhopper.Components.Params.Input.GraphMapper import map_graph_tree
from pyhopper.Components.Params.Input.Panel import parse_panel_lines, parse_panel_text
from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path as TreePath


class SpecialInputComponentTests(unittest.TestCase):
    def test_boolean_toggle_emits_one_boolean_item(self):
        result = BooleanToggle()
        self.assertEqual(result.all_items(), [False])

    def test_md_slider_emits_one_atomic_vector(self):
        result = MDSlider()
        self.assertEqual(result.all_items(), [AtomicVector(0.5, 0.5, 0.0)])

    def test_graph_mapper_preserves_tree_paths_and_item_counts(self):
        source = DataTree.from_branches({
            TreePath(0): [0.0, 0.5, 1.0],
            TreePath(2): [0.25],
        })
        mapped = map_graph_tree(source, {"graphType": "sine"})
        self.assertEqual(mapped.paths, source.paths)
        self.assertEqual([len(branch) for _, branch in mapped.branches()], [3, 1])
        self.assertAlmostEqual(mapped.branch(TreePath(0))[1], 0.5)

    def test_graph_mapper_component_default_is_one_to_one(self):
        result = GraphMapper([0.0, 0.5, 1.0])
        self.assertEqual(len(result), 3)

    def test_number_slider_settings_are_backend_authoritative(self):
        result = NumberSlider(_settings={
            "value": 4.74,
            "min": 0.0,
            "max": 10.0,
            "decimals": 2,
            "rounding": "integer",
        })

        self.assertEqual(result.all_items(), [5.0])

    def test_point_on_curve_uses_normalized_length_and_preserves_paths(self):
        source = DataTree.from_branches({
            TreePath(0): [AtomicLine(AtomicPoint(0, 0, 0), AtomicPoint(10, 0, 0))],
            TreePath(2): [AtomicLine(AtomicPoint(0, 0, 0), AtomicPoint(0, 4, 0))],
        })

        result = PointOnCurve(source, 0.25)

        self.assertEqual(result.paths, source.paths)
        self.assertEqual(result.branch(TreePath(0))[0], AtomicPoint(2.5, 0.0, 0.0))
        self.assertEqual(result.branch(TreePath(2))[0], AtomicPoint(0.0, 1.0, 0.0))

    def test_panel_text_parser_only_infers_unambiguous_single_line_scalars(self):
        self.assertEqual(parse_panel_text("25"), 25)
        self.assertEqual(parse_panel_text("-25"), -25)
        self.assertEqual(parse_panel_text("25.5"), 25.5)
        self.assertEqual(parse_panel_text("1e3"), 1000.0)
        self.assertIs(parse_panel_text("true"), True)
        self.assertIs(parse_panel_text("FALSE"), False)
        self.assertEqual(parse_panel_text("25f"), "25f")
        self.assertEqual(parse_panel_text("25\n25"), "25\n25")

    def test_panel_line_parser_emits_individually_typed_items(self):
        self.assertEqual(parse_panel_lines("25\n16\n13"), [25, 16, 13])
        self.assertEqual(parse_panel_lines("true\r\nlabel\r\n"), [True, "label", ""])

    def test_compiler_emits_authored_special_values(self):
        def node(node_id: str, component_key: str, name: str, values: dict):
            return {
                "id": node_id,
                "kind": "component",
                "componentKey": component_key,
                "component": {"tab": "Params", "category": "Input", "name": name},
                "position": {"x": 0, "y": 0},
                "previewEnabled": True,
                "values": values,
                "portOperations": {},
            }

        document = {
            "schemaVersion": 2,
            "graphId": "special-node-test",
            "viewport": {"x": 0, "y": 0, "zoom": 1},
            "scene": {
                "schemaVersion": 3,
                "objects": {
                    "line": {
                        "id": "line",
                        "name": "Line",
                        "atom": AtomicLine(
                            AtomicPoint(0.0, 0.0, 0.0),
                            AtomicPoint(8.0, 0.0, 0.0),
                        ).to_json(),
                        "transform": AtomicTransform.identity().to_json(),
                    },
                },
            },
            "nodes": [
                node("toggle", "pyhopper.Components.Params.Input.BooleanToggle.BooleanToggle", "BooleanToggle", {"value": True}),
                node("md", "pyhopper.Components.Params.Input.MDSlider.MDSlider", "MDSlider", {"x": 0.2, "y": 0.8}),
                node("slider", "pyhopper.Components.Params.Input.NumberSlider.NumberSlider", "NumberSlider", {"value": 0.5}),
                node(
                    "mapper",
                    "pyhopper.Components.Params.Input.GraphMapper.GraphMapper",
                    "GraphMapper",
                    {"graphType": "linear", "xMin": 0, "xMax": 1, "yMin": 10, "yMax": 20},
                ),
                node(
                    "panel",
                    "pyhopper.Components.Params.Input.Panel.Panel",
                    "Panel",
                    {"text": "12\nfixed value", "textAlign": "center"},
                ),
                node(
                    "viewer",
                    "pyhopper.Components.Params.Input.Panel.Panel",
                    "Panel",
                    {"text": "ignored while connected"},
                ),
                node(
                    "integer-panel",
                    "pyhopper.Components.Params.Input.Panel.Panel",
                    "Panel",
                    {"text": "25"},
                ),
                node(
                    "boolean-panel",
                    "pyhopper.Components.Params.Input.Panel.Panel",
                    "Panel",
                    {"text": "true"},
                ),
                node(
                    "multiline-panel",
                    "pyhopper.Components.Params.Input.Panel.Panel",
                    "Panel",
                    {"text": "25\n16\ntrue\nlabel", "multilineData": True},
                ),
                node(
                    "curve-point",
                    "pyhopper.Components.Curve.Analysis.PointOnCurve.PointOnCurve",
                    "PointOnCurve",
                    {"parameter": 0.25},
                ),
                {
                    "id": "line-reference",
                    "kind": "object-reference",
                    "objectId": "line",
                    "position": {"x": 0, "y": 0},
                    "previewEnabled": True,
                    "values": {},
                    "portOperations": {},
                },
            ],
            "edges": [
                {
                    "id": "slider-mapper",
                    "sourceNodeId": "slider",
                    "sourcePort": "value",
                    "targetNodeId": "mapper",
                    "targetPort": "numbers",
                },
                {
                    "id": "mapper-viewer",
                    "sourceNodeId": "mapper",
                    "sourcePort": "mapped",
                    "targetNodeId": "viewer",
                    "targetPort": "data",
                },
                {
                    "id": "line-curve-point",
                    "sourceNodeId": "line-reference",
                    "sourcePort": "geometry",
                    "targetNodeId": "curve-point",
                    "targetPort": "curve",
                },
            ],
        }
        compiled = compile_graph_document(document)
        namespace: dict = {}
        exec(compiled.source, namespace, namespace)
        outputs = namespace[compiled.node_outputs_entrypoint]()
        self.assertEqual(outputs["toggle"].all_items(), [True])
        self.assertEqual(outputs["md"].all_items(), [AtomicVector(0.2, 0.8, 0.0)])
        self.assertEqual(outputs["mapper"].all_items(), [15.0])
        self.assertEqual(outputs["panel"].all_items(), ["12\nfixed value"])
        self.assertEqual(outputs["viewer"].all_items(), [15.0])
        self.assertEqual(outputs["integer-panel"].all_items(), [25])
        self.assertEqual(outputs["boolean-panel"].all_items(), [True])
        self.assertEqual(outputs["multiline-panel"].paths, [TreePath(0)])
        self.assertEqual(outputs["multiline-panel"].all_items(), [25, 16, True, "label"])
        self.assertEqual(outputs["curve-point"].all_items(), [AtomicPoint(2.0, 0.0, 0.0)])


if __name__ == "__main__":
    unittest.main()
