"""Curve parameterisation layer, frames, arcs and rounded rectangles (Wave A5 kernel additions).

The numbers come from the Grasshopper probes recorded while building the wave
(rhino-test/oracle/cases/Curve/*.json hold the full comparisons).
"""

from __future__ import annotations

import math
import unittest

from pyhopper.Components.Curve.Primitive._rectangles import make_rectangle
from pyhopper.Core.Atoms import AtomicArc, AtomicCircle, AtomicInterval, AtomicLine, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicPolyline, AtomicRectangle, AtomicVector
from pyhopper.Utils.Arcs import arc_from_plane, arc_from_start_end_direction, arc_from_three_points
from pyhopper.Utils.Curves import (
    curve_domain_of,
    curve_is_closed,
    curve_is_periodic,
    curve_kink_angle,
    curve_length_at,
    curve_parameter_at_length,
    curve_point_at,
    curve_tangent_at,
    divide_curve_by_count,
    divide_curve_by_length,
)
from pyhopper.Utils.Frames import curve_perpendicular_frames, initial_frame_axis

P = AtomicPoint
V = AtomicVector
CIRCLE = AtomicCircle(AtomicPlane.world_xy(), 2.0)
POLY = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0)))
HELIX = AtomicNurbsCurve((P(0, 0, 0), P(2, 0, 1), P(2, 2, 2), P(0, 2, 3), P(0, 0, 4), P(2, 0, 5)), (1.0,) * 6, (0, 0, 0, 0, 1, 2, 3, 3, 3, 3), 3)


def close(test, actual, expected, places=6):
    for a, e in zip((actual.x, actual.y, actual.z), expected):
        test.assertAlmostEqual(a, e, places=places)


class ParameterisationTests(unittest.TestCase):
    def test_named_atoms_live_on_unit_domain_and_nurbs_on_their_knots(self):
        self.assertEqual(curve_domain_of(CIRCLE), (0.0, 1.0))
        self.assertEqual(curve_domain_of(POLY), (0.0, 1.0))
        self.assertEqual(curve_domain_of(HELIX), (0.0, 3.0))

    def test_arcs_are_parameterised_by_angle(self):
        close(self, curve_point_at(CIRCLE, 0.1), (2 * math.cos(0.2 * math.pi), 2 * math.sin(0.2 * math.pi), 0.0))
        close(self, curve_tangent_at(CIRCLE, 0.25), (-1.0, 0.0, 0.0))

    def test_polylines_are_uniform_per_segment(self):
        uneven = AtomicPolyline((P(0, 0, 0), P(1, 0, 0), P(4, 0, 0)))
        close(self, curve_point_at(uneven, 0.75), (2.5, 0.0, 0.0))
        self.assertAlmostEqual(curve_length_at(uneven, 0.75), 2.5)
        self.assertAlmostEqual(curve_parameter_at_length(uneven, 1.5), 0.5 + 0.5 / 6.0)

    def test_kink_angle_and_tangent_sides(self):
        self.assertAlmostEqual(curve_kink_angle(POLY, 0.5), math.pi / 2)
        self.assertEqual(curve_kink_angle(POLY, 0.25), 0.0)
        close(self, curve_tangent_at(POLY, 0.5), (0.0, 1.0, 0.0))
        close(self, curve_tangent_at(POLY, 0.5, incoming=True), (1.0, 0.0, 0.0))
        closed = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(0, 2, 0), P(0, 0, 0)))
        self.assertAlmostEqual(curve_kink_angle(closed, 0.0), math.pi / 2)

    def test_closed_and_periodic(self):
        self.assertTrue(curve_is_closed(CIRCLE) and curve_is_periodic(CIRCLE))
        self.assertFalse(curve_is_periodic(HELIX))
        periodic = AtomicNurbsCurve((P(1, 0, 0), P(0, 1, 0), P(-1, 0, 0), P(0, -1, 0), P(1, 0, 0), P(0, 1, 0), P(-1, 0, 0)), (1.0,) * 7, (-3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7), 3)
        self.assertTrue(curve_is_closed(periodic) and curve_is_periodic(periodic))


class DivisionTests(unittest.TestCase):
    def test_divide_by_count_parameters_follow_the_atom(self):
        _, _, parameters = divide_curve_by_count(CIRCLE, 3)
        self.assertEqual([round(t, 12) for t in parameters], [0.0, round(1 / 3, 12), round(2 / 3, 12)])

    def test_divide_by_length_rules(self):
        line = AtomicLine(P(0, 0, 0), P(4, 0, 0))
        self.assertEqual(divide_curve_by_length(line, 1.5)[2], [0.0, 0.375, 0.75])
        self.assertEqual(divide_curve_by_length(line, 2.0)[2], [0.0, 0.5, 1.0])  # exact end included
        self.assertEqual(divide_curve_by_length(CIRCLE, math.pi)[2], [0.0, 0.25, 0.5, 0.75])  # seam not repeated
        self.assertEqual(len(divide_curve_by_length(line, 9.0)[0]), 1)
        with self.assertRaises(ValueError):
            divide_curve_by_length(line, 0.0)


class FrameTests(unittest.TestCase):
    def test_initial_axis_rules(self):
        close(self, initial_frame_axis(V(1, 0, 0)), (0.0, 0.0, 1.0))  # straight: world Z
        close(self, initial_frame_axis(V(0, 0, 1)), (1.0, 0.0, 0.0))  # vertical: world X
        close(self, initial_frame_axis(V(0, 1, 0), V(-0.5, 0, 0)), (-1.0, 0.0, 0.0))  # curvature wins

    def test_aligned_helix_frames_match_grasshopper(self):
        _, _, parameters = divide_curve_by_count(HELIX, 4)
        frames = curve_perpendicular_frames(HELIX, parameters)
        grasshopper_x = [
            (-0.18257418583505539, 0.9128709291752768, 0.36514837167011077),
            (-0.7810203687812965, 0.6149496064754377, -0.108830901146834),
            (-0.5931467192190806, -0.15071100175074068, -0.790862291066485),
            (-0.6095025865616498, -0.7191093789992907, -0.3337488546945337),
            (-0.05263039782882556, -0.9930509584718691, 0.10526079565765112),
        ]
        for frame, expected in zip(frames, grasshopper_x):
            close(self, frame.x_axis, expected, places=5)

    def test_unaligned_frames_use_rhino_default_axis(self):
        frames = curve_perpendicular_frames(AtomicLine(P(0, 0, 0), P(4, 0, 0)), [0.0, 1.0], align=False)
        close(self, frames[0].x_axis, (0.0, 1.0, 0.0))
        close(self, frames[0].normal, (1.0, 0.0, 0.0))


class ArcTests(unittest.TestCase):
    def test_three_point_arcs(self):
        arc, plane, radius = arc_from_three_points(P(1, 0, 0), P(0, 1, 1), P(-1, 0, 2))
        self.assertAlmostEqual(radius, 1.5)
        close(self, plane.origin, (0.0, -0.5, 1.0))
        self.assertAlmostEqual(arc.angle.end, 2.4619188346815495)
        line, _, radius = arc_from_three_points(P(0, 0, 0), P(1, 0, 0), P(2, 0, 0))
        self.assertIsInstance(line, AtomicLine)
        self.assertEqual(radius, math.inf)

    def test_start_end_direction_arc(self):
        arc, plane, radius = arc_from_start_end_direction(P(0, 0, 0), P(2, 0, 0), V(1, 1, 0))
        self.assertAlmostEqual(radius, math.sqrt(2))
        close(self, plane.origin, (1.0, -1.0, 0.0))
        close(self, plane.normal, (0.0, 0.0, -1.0))
        self.assertAlmostEqual(arc.angle.end, math.pi / 2)

    def test_reversed_domain_flips_the_plane(self):
        arc = arc_from_plane(AtomicPlane.world_xy(), 2.0, AtomicInterval(math.pi, 0.0))
        close(self, arc.plane.normal, (0.0, 0.0, -1.0))
        self.assertEqual((arc.angle.start, arc.angle.end), (-math.pi, 0.0))


class RoundedRectangleTests(unittest.TestCase):
    def test_exact_fillet_curve_structure(self):
        curve, length = make_rectangle(AtomicPlane.world_xy(), 4.0, 2.0, 0.5)
        self.assertEqual([type(segment).__name__ for segment in curve.segments], ["AtomicLine", "AtomicArc"] * 4)
        self.assertAlmostEqual(sum(curve.spans), length)
        self.assertAlmostEqual(length, 2 * (4 + 2) - 8 * 0.5 + 2 * math.pi * 0.5)
        close(self, curve_point_at(curve, 0.0), (-1.5, -1.0, 0.0))
        clamped, _ = make_rectangle(AtomicPlane.world_xy(), 4.0, 2.0, 5.0)
        self.assertEqual([type(segment).__name__ for segment in clamped.segments], ["AtomicLine", "AtomicArc", "AtomicArc"] * 2)  # the short edges vanish

    def test_sharp_rectangle_stays_a_rectangle(self):
        rectangle, length = make_rectangle(AtomicPlane.world_xy(), 3.0, 2.0)
        self.assertIsInstance(rectangle, AtomicRectangle)
        self.assertEqual(length, 10.0)


if __name__ == "__main__":
    unittest.main()


class WaveB4FittingTests(unittest.TestCase):
    """Curve fitting helpers behind Fit Line, Circle Fit, Rebuild, Catenary and Curve To Polyline."""

    def test_fit_circle_matches_grasshopper_geometric_fit(self):
        from pyhopper.Core.Atoms import AtomicPoint
        from pyhopper.Utils.CurveFitting import fit_circle

        circle, deviation = fit_circle([AtomicPoint(2, 0, 0), AtomicPoint(0, 2, 0), AtomicPoint(-2, 0, 0), AtomicPoint(0, -2.2, 0)])
        self.assertAlmostEqual(circle.plane.origin.y, -0.10249177939650633, places=9)
        self.assertAlmostEqual(circle.radius, 2.051312209658389, places=9)
        self.assertAlmostEqual(deviation, 0.05117956973811699, places=9)

    def test_rebuild_reproduces_a_line_and_keeps_structure(self):
        from pyhopper.Core.Atoms import AtomicArc, AtomicInterval, AtomicLine, AtomicPlane, AtomicPoint
        from pyhopper.Utils.CurveFitting import rebuild_curve

        line = rebuild_curve(AtomicLine(AtomicPoint(0, 0, 0), AtomicPoint(4, 0, 0)), 3)
        self.assertEqual([(p.x, p.y, p.z) for p in line.control_points], [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (4.0, 0.0, 0.0)])
        self.assertEqual(line.knots, (0.0, 0.0, 1.0, 2.0, 2.0))
        arc = rebuild_curve(AtomicArc(AtomicPlane.world_xy(), 2.0, AtomicInterval(0.0, math.pi / 2)), 5, 2)
        self.assertEqual((len(arc.control_points), arc.degree, arc.knots), (5, 2, (0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 3.0, 3.0)))
        self.assertAlmostEqual(math.hypot(arc.control_points[2].x, arc.control_points[2].y), 2.07, places=2)  # middle control point sits just outside the arc

    def test_catenary_hangs_with_the_requested_length(self):
        from pyhopper.Core.Atoms import AtomicPoint, AtomicPolyline, AtomicVector
        from pyhopper.Utils.CurveFitting import catenary_points
        from pyhopper.Utils.Curves import curve_length

        points = catenary_points(AtomicPoint(0, 0, 0), AtomicPoint(4, 0, 0), 6.0, AtomicVector(0, 0, -1))
        self.assertEqual(len(points), 50)
        self.assertAlmostEqual(curve_length(AtomicPolyline(tuple(points))), 6.0, places=2)
        self.assertLess(min(p.z for p in points), -2.0)
        self.assertIsNone(catenary_points(AtomicPoint(0, 0, 0), AtomicPoint(4, 0, 0), 3.0, AtomicVector(0, 0, -1)))

    def test_curve_to_polyline_segment_counts_match_grasshopper(self):
        from pyhopper.Core.Atoms import AtomicArc, AtomicCircle, AtomicInterval, AtomicPlane
        from pyhopper.Utils.CurveFitting import curve_to_polyline

        arc = AtomicArc(AtomicPlane.world_xy(), 2.0, AtomicInterval(0.0, math.pi / 2))
        self.assertEqual(len(curve_to_polyline(arc, 0.1).points) - 1, 3)
        self.assertEqual(len(curve_to_polyline(arc, 0.01).points) - 1, 8)
        self.assertEqual(len(curve_to_polyline(AtomicCircle(AtomicPlane.world_xy(), 1.5), 0.1, max_edge=1.0).points) - 1, 10)
