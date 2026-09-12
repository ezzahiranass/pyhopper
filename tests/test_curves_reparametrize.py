"""Reparametrize: curve domains map to [0, 1]; the port operation compiles and runs."""

from __future__ import annotations

import unittest

from tests.support.trees import tree
from tests.test_runtime_compiler import CONSTRUCT_POINT, INTERPOLATE, LENGTH, SERIES, document, edge, node, run

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicControlPointCurve,
    AtomicEllipse,
    AtomicInterpolatedCurve,
    AtomicInterval,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicRectangle,
)
from pyhopper.Core.TypeSystem import CURVE_TYPES
from pyhopper.Graph.runtime import PORT_OP_FUNCTIONS, PORT_OP_METHODS, VALID_PORT_OPERATIONS
from pyhopper.Utils.Curves import (
    evaluate_nurbs_curve,
    nurbs_curve_domain,
    reparametrize_curve,
    reparametrize_nurbs_curve,
    reparametrize_tree,
)
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

P = AtomicPoint


def _shifted_curve() -> AtomicNurbsCurve:
    """A degree-2 curve whose knot domain is [2, 6] rather than [0, 1]."""
    return AtomicNurbsCurve(
        control_points=(P(0, 0, 0), P(1, 2, 0), P(3, 2, 1), P(4, 0, 0)),
        weights=(1.0, 1.0, 1.0, 1.0),
        knots=(2.0, 2.0, 2.0, 4.0, 6.0, 6.0, 6.0),
        degree=2,
    )


class ReparametrizeTests(unittest.TestCase):
    def test_domain_becomes_unit_interval_and_geometry_is_unchanged(self):
        curve = _shifted_curve()
        result = reparametrize_nurbs_curve(curve)
        self.assertEqual(nurbs_curve_domain(result), (0.0, 1.0))
        for t in (0.0, 0.2, 0.5, 0.75, 1.0):
            before = evaluate_nurbs_curve(curve, 2.0 + 4.0 * t)
            after = evaluate_nurbs_curve(result, t)
            self.assertAlmostEqual(before.x, after.x, places=12)
            self.assertAlmostEqual(before.y, after.y, places=12)
            self.assertAlmostEqual(before.z, after.z, places=12)

    def test_zero_length_domain_raises(self):
        degenerate = AtomicNurbsCurve(control_points=(P(0, 0, 0), P(1, 0, 0)), weights=(1.0, 1.0), knots=(3.0, 3.0, 3.0, 3.0), degree=1)
        with self.assertRaises(ValueError):
            reparametrize_nurbs_curve(degenerate)

    def test_non_nurbs_items_pass_through(self):
        line = AtomicLine(P(0, 0, 0), P(1, 0, 0))
        self.assertIs(reparametrize_curve(line), line)
        self.assertEqual(reparametrize_curve(3.5), 3.5)

    def test_every_named_curve_atom_already_unifies_to_the_unit_domain(self):
        plane = AtomicPlane.world_xy()
        samples = {
            AtomicLine: AtomicLine(P(0, 0, 0), P(3, 0, 0)),
            AtomicCircle: AtomicCircle(plane, 2.0),
            AtomicArc: AtomicArc(plane, 2.0, AtomicInterval(0.2, 2.0)),
            AtomicPolyline: AtomicPolyline((P(0, 0, 0), P(1, 1, 0), P(2, 0, 0))),
            AtomicNurbsCurve: as_nurbs_curve(AtomicCircle(plane, 1.0)),
            AtomicEllipse: AtomicEllipse(plane, 2.0, 1.0),
            AtomicRectangle: AtomicRectangle(plane, 2.0, 1.0),
            AtomicInterpolatedCurve: AtomicInterpolatedCurve((P(0, 0, 0), P(1, 1, 0), P(2, 0, 0))),
            AtomicControlPointCurve: AtomicControlPointCurve((P(0, 0, 0), P(1, 1, 0), P(2, 0, 0)), 2),
        }
        self.assertEqual(set(samples), set(CURVE_TYPES), "add a sample for every CURVE_TYPES member")
        for atom_type, atom in samples.items():
            with self.subTest(atom=atom_type.__name__):
                self.assertEqual(nurbs_curve_domain(as_nurbs_curve(atom)), (0.0, 1.0))

    def test_tree_helper_preserves_paths(self):
        result = reparametrize_tree(tree({"0": [_shifted_curve()], "3;1": [5.0]}))
        self.assertEqual([str(p) for p in result.paths], ["{0}", "{3;1}"])
        self.assertEqual(nurbs_curve_domain(result.branch(result.paths[0])[0]), (0.0, 1.0))
        self.assertEqual(list(result.branch(result.paths[1])), [5.0])


class ReparametrizePortOperationTests(unittest.TestCase):
    def test_operation_is_registered_as_a_function_not_a_method(self):
        self.assertIn("Reparametrize", VALID_PORT_OPERATIONS)
        self.assertNotIn("Reparametrize", PORT_OP_METHODS)
        self.assertEqual(PORT_OP_FUNCTIONS["Reparametrize"], ("pyhopper.Utils.Curves", "reparametrize_tree"))

    def test_graph_with_reparametrize_input_operation_compiles_and_executes(self):
        doc = document(
            [
                node("s", SERIES, preview=False),
                node("p", CONSTRUCT_POINT, preview=False),
                node("pl", INTERPOLATE, preview=False),
                node("len", LENGTH, port_operations={"input:curve": "Reparametrize"}),
            ],
            [
                edge("e0", "s", "series", "p", "x_coordinate"),
                edge("e1", "p", "point", "pl", "vertices"),
                edge("e2", "pl", "curve", "len", "curve"),
            ],
        )
        compiled, outputs, _ = run(doc)
        self.assertIn("from pyhopper.Utils.Curves import reparametrize_tree", compiled.source)
        self.assertIn("Length(curve=reparametrize_tree(node_002_interpolate))", compiled.source)
        self.assertAlmostEqual(outputs["len"].all_items()[0], 9.0, places=6)

    def test_reparametrize_output_operation_uses_its_own_variable(self):
        doc = document(
            [
                node("s", SERIES, preview=False),
                node("p", CONSTRUCT_POINT, preview=False),
                node("pl", INTERPOLATE, port_operations={"output:curve": "Reparametrize"}),
            ],
            [edge("e0", "s", "series", "p", "x_coordinate"), edge("e1", "p", "point", "pl", "vertices")],
        )
        compiled, outputs, _ = run(doc)
        self.assertIn("node_002_interpolate__curve = reparametrize_tree(node_002_interpolate)", compiled.source)
        self.assertEqual(nurbs_curve_domain(outputs["pl"].all_items()[0]), (0.0, 1.0))


if __name__ == "__main__":
    unittest.main()
