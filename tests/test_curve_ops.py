"""Polycurves, NURBS editing and the curve operations behind the K2+K5 wave.

Expected numbers come from the Grasshopper 8 probes recorded while building the
wave (rhino-test/oracle/cases/Curve/*.json hold the full comparisons).
"""

from __future__ import annotations

import math
import unittest

from pyhopper.Core.Atoms import AtomicArc, AtomicCircle, AtomicInterval, AtomicLine, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicPolyCurve, AtomicPolyline, AtomicSurface, AtomicTransform, AtomicVector, atom_from_json
from pyhopper.Utils.CurveOps import blend_curve, blend_curve_through_point, change_seam, dash_pattern, explode, extend_curve, fillet_at, fillet_distance, fillet_radius, join_curves, polyarc, shatter, sub_curve, tangent_curve
from pyhopper.Utils.Curves import curve_derivatives_at, curve_domain_of, curve_length, curve_length_at, curve_parameter_at_length, curve_point_at, curve_tangent_at, nurbs_curve_length, reparametrize_curve
from pyhopper.Utils.NurbsEditing import elevate_degree, extend_nurbs_domain, insert_knot, join_nurbs_curves, split_nurbs_curve, sub_nurbs_curve, sub_surface
from pyhopper.Utils.Nurbs import curve_point, surface_point
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

P, V = AtomicPoint, AtomicVector


def nurbs(points, degree=3, knots=None):
    count = len(points)
    if knots is None:
        knots = [0.0] * (degree + 1) + [i / (count - degree) for i in range(1, count - degree)] + [1.0] * (degree + 1)
    return AtomicNurbsCurve(tuple(P(*p) for p in points), (1.0,) * count, tuple(float(k) for k in knots), degree)


CUBIC = nurbs([(0, 0, 0), (1, 2, 0), (3, 2, 1), (4, 0, 0)])
KNOTTED = nurbs([(0, 0, 0), (1, 2, 0), (2, 2, 0), (3, 0, 0), (4, 0, 0), (5, 2, 0), (6, 2, 0)], 3, [0, 0, 0, 0, 0.5, 0.5, 0.5, 1, 1, 1, 1])
CIRCLE = AtomicCircle(AtomicPlane.world_xy(), 2.0)
ARC = AtomicArc(AtomicPlane.world_xy(), 2.0, AtomicInterval(0.0, math.pi / 2))
LINE = AtomicLine(P(0, 0, 0), P(4, 0, 0))
LINE2 = AtomicLine(P(2, -3, 0), P(2, 0, 0))
PLINE = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(4, 2, 0)))
CLOSED_PL = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(0, 2, 0), P(0, 0, 0)))
LINE_A, LINE_B = AtomicLine(P(0, 0, 0), P(2, 0, 0)), AtomicLine(P(4, 2, 0), P(6, 2, 0))
POLY = AtomicPolyCurve((LINE2, ARC), (3.0, math.pi), 0.0)


def close(test, actual, expected, places=6):
    for a, e in zip((actual.x, actual.y, actual.z), expected):
        test.assertAlmostEqual(a, e, places=places)


class PolyCurveTests(unittest.TestCase):
    def test_domain_evaluation_and_length_follow_the_spans(self):
        self.assertEqual(curve_domain_of(POLY), (0.0, 3.0 + math.pi))
        close(self, curve_point_at(POLY, 1.5), (2.0, -1.5, 0.0))
        close(self, curve_point_at(POLY, 3.0 + math.pi / 2), (2 * math.cos(math.pi / 4), 2 * math.sin(math.pi / 4), 0.0))  # halfway round the arc
        self.assertAlmostEqual(curve_length(POLY), 3.0 + math.pi)
        self.assertAlmostEqual(curve_length_at(POLY, 3.0 + math.pi / 2), 3.0 + math.pi / 2)
        self.assertAlmostEqual(curve_parameter_at_length(POLY, 4.0), 4.0)
        close(self, curve_tangent_at(POLY, 1.0), (0, 1, 0))
        close(self, curve_tangent_at(POLY, 3.0), (0, 1, 0))  # the joint belongs to the outgoing arc, whose start tangent is +y
        _, first, _, _ = curve_derivatives_at(POLY, 4.0)
        self.assertAlmostEqual(math.hypot(first.x, first.y), 2.0 * (math.pi / 2) / math.pi)  # arc speed scaled onto its span

    def test_json_transform_reparametrize_and_nurbs_form(self):
        self.assertEqual(atom_from_json(POLY.to_json()), POLY)
        moved = apply_transform(AtomicTransform.translation(V(1, 0, 0)), POLY)
        self.assertEqual(moved.spans, POLY.spans)
        close(self, curve_point_at(moved, 0.0), (3.0, -3.0, 0.0))
        unit = reparametrize_curve(POLY)
        self.assertEqual(curve_domain_of(unit), (0.0, 1.0))
        close(self, curve_point_at(unit, 3.0 / (3.0 + math.pi)), (2, 0, 0))
        joined = as_nurbs_curve(POLY)
        self.assertEqual(joined.degree, 2)
        close(self, curve_point(joined, 3.0), (2, 0, 0))
        close(self, curve_point(joined, 3.0 + math.pi), (0, 2, 0))


class NurbsEditingTests(unittest.TestCase):
    def test_knot_insertion_and_splitting_keep_the_geometry(self):
        refined = insert_knot(CUBIC, 0.3, 3)
        self.assertEqual(len(refined.control_points), 7)
        for t in (0.1, 0.3, 0.8):
            close(self, curve_point(refined, t), tuple(getattr(curve_point(CUBIC, t), a) for a in "xyz"), 9)
        left, right = split_nurbs_curve(CUBIC, 0.3)
        self.assertEqual(left.knots, (0.0,) * 4 + (0.3,) * 4)
        close(self, left.control_points[-1], (1.116, 1.26, 0.189), 9)  # Grasshopper's Shatter
        close(self, right.control_points[0], (1.116, 1.26, 0.189), 9)
        close(self, sub_nurbs_curve(CUBIC, 0.3, 0.6).control_points[1], (1.542, 1.5, 0.288), 9)
        piece = sub_nurbs_curve(CUBIC, 0.2, 0.7)
        close(self, piece.control_points[0], (0.704, 0.96, 0.096), 9)
        close(self, piece.control_points[-1], (2.884, 1.26, 0.441), 9)

    def test_degree_elevation_and_joining(self):
        quintic = elevate_degree(CUBIC, 5)
        self.assertEqual((quintic.degree, len(quintic.control_points)), (5, 6))
        for t in (0.15, 0.5, 0.95):
            close(self, curve_point(quintic, t), tuple(getattr(curve_point(CUBIC, t), a) for a in "xyz"), 9)
        rational = elevate_degree(as_nurbs_curve(ARC), 4)
        close(self, curve_point(rational, 0.5), tuple(getattr(curve_point(as_nurbs_curve(ARC), 0.5), a) for a in "xyz"), 9)
        joined = join_nurbs_curves([CUBIC, as_nurbs_curve(AtomicLine(P(4, 0, 0), P(6, 0, 0)))], [0.0, 1.0, 3.0])
        self.assertEqual(joined.knots, (0.0,) * 4 + (1.0,) * 3 + (3.0,) * 4)
        close(self, curve_point(joined, 2.0), (5, 0, 0), 9)

    def test_smooth_extension_matches_grasshopper(self):
        extended = extend_nurbs_domain(CUBIC, -0.13672509106160183, 1.0644253369922625)
        close(self, extended.control_points[0], (-0.3489822, -0.9325130, 0.0637490))
        close(self, extended.control_points[1], (0.4788054, 2.1266974, -0.3320679))
        close(self, extended.control_points[3], (4.1802893, -0.4114558, -0.2189820))
        kinked = extend_nurbs_domain(KNOTTED, -0.06719897320973836, 1.0)
        close(self, kinked.control_points[0], (-0.4031938, -0.9147645, 0.0))
        close(self, kinked.control_points[3], (3, 0, 0), 9)  # untouched beyond the first span
        self.assertEqual(kinked.knots[4:7], (0.5, 0.5, 0.5))

    def test_sub_surface_is_grasshoppers_isotrim(self):
        dome = AtomicSurface(poles=tuple(tuple(P(*p) for p in row) for row in [[(0, 0, 0), (2, 0, 1), (4, 0, 0)], [(0, 2, 1), (2, 2, 3), (4, 2, 1)], [(0, 4, 0), (2, 4, 1), (4, 4, 0)]]),
                             weights=((1.0,) * 3,) * 3, u_knots=(0.0, 1.0), v_knots=(0.0, 1.0), u_mults=(3, 3), v_mults=(3, 3), u_degree=2, v_degree=2)
        patch = sub_surface(dome, (0.75, 0.25), (0.0, 0.5))
        self.assertEqual((patch.u_knots, patch.v_knots), ((0.25, 0.75), (0.0, 0.5)))
        close(self, patch.poles[1][1], (2.0, 1.0, 1.4375), 9)
        close(self, surface_point(patch, 0.5, 0.4), tuple(getattr(surface_point(dome, 0.5, 0.4), a) for a in "xyz"), 9)


class CurveOperationTests(unittest.TestCase):
    def test_shatter_and_sub_curve(self):
        pieces = shatter(CUBIC, [0.6, 0.3, 0.3, 1.5])
        self.assertEqual([p.knots[0] for p in pieces], [0.0, 0.3, 0.6])
        arc, wrap = shatter(CIRCLE, [0.5 / (2 * math.pi), 1.5 / (2 * math.pi)])
        self.assertEqual((round(arc.angle.start, 9), round(arc.angle.end, 9)), (0.5, 1.5))
        self.assertIsInstance(wrap, AtomicPolyCurve)
        self.assertEqual(len(wrap.segments), 2)
        self.assertEqual(shatter(CUBIC, []), [])
        self.assertEqual(shatter(LINE, [0.0, 1.0]), [LINE])
        self.assertEqual(sub_curve(PLINE, 0.5 / 3, 2.5 / 3).points, (P(1, 0, 0), P(2, 0, 0), P(2, 2, 0), P(3, 2, 0)))
        piece = sub_curve(POLY, 1.0, 5.0)
        self.assertEqual(piece.start, 1.0)
        self.assertAlmostEqual(sum(piece.spans), 4.0)

    def test_explode(self):
        segments, vertices = explode(KNOTTED)
        self.assertEqual(len(segments), 2)
        self.assertEqual(vertices, [P(0, 0, 0), P(3, 0, 0), P(6, 2, 0)])
        self.assertEqual(explode(CLOSED_PL)[1][-1], P(0, 0, 0))
        nested = AtomicPolyCurve((POLY, AtomicLine(P(0, 2, 0), P(0, 5, 0))), (3.0 + math.pi, 3.0), 0.0)
        self.assertEqual(len(explode(nested, True)[0]), 3)
        self.assertEqual(len(explode(nested, False)[0]), 2)

    def test_extend(self):
        lines = extend_curve(LINE, 0, 1.0, 2.0)
        self.assertEqual(lines.spans, (0.25, 1.0, 0.5))
        self.assertEqual(lines.start, -0.25)
        close(self, curve_point_at(lines, -0.25), (-1, 0, 0))
        arcs = extend_curve(ARC, 1, 1.0, 2.0)
        self.assertAlmostEqual(arcs.segments[0].angle.start, -0.5)
        self.assertAlmostEqual(arcs.segments[2].angle.end, 1.0)
        smooth = extend_curve(CUBIC, 2, 1.0, 0.0)
        self.assertAlmostEqual(smooth.knots[0], -0.13672509106160183, places=6)
        self.assertAlmostEqual(nurbs_curve_length(sub_nurbs_curve(smooth, smooth.knots[0], 0.0)), 1.0, places=6)
        trimmed = extend_curve(CUBIC, 0, -1.0, -0.5)
        self.assertAlmostEqual(trimmed.knots[0], 0.163294897, places=6)
        self.assertEqual(extend_curve(CIRCLE, 0, 1.0, 1.0), CIRCLE)
        self.assertEqual(extend_curve(PLINE, 2, 1.0, 1.0).points[0], P(-1, 0, 0))

    def test_seam(self):
        close(self, change_seam(CIRCLE, 0.5 / (2 * math.pi)).plane.x_axis, (math.cos(0.5), math.sin(0.5), 0.0))
        self.assertEqual(change_seam(CLOSED_PL, 0.125).points, (P(1, 0, 0), P(2, 0, 0), P(2, 2, 0), P(0, 2, 0), P(0, 0, 0), P(1, 0, 0)))
        closed = nurbs([(0, 0, 0), (3, 0, 0), (3, 3, 0), (0, 3, 0), (0, 0, 0)])
        self.assertEqual(change_seam(closed, 0.3).knots, (0.0,) * 4 + (0.2,) + (0.7,) * 3 + (1.0,) * 4)
        self.assertEqual(change_seam(CUBIC, 0.5), CUBIC)

    def test_join(self):
        joined = join_curves([ARC, LINE2])[0]
        self.assertEqual([type(s).__name__ for s in joined.segments], ["AtomicLine", "AtomicArc"])
        self.assertEqual(joined.spans, (3.0, math.pi))
        flipped = join_curves([AtomicLine(P(2, 0, 0), P(2, -3, 0)), ARC])[0]
        self.assertEqual(type(flipped.segments[0]).__name__, "AtomicArc")
        self.assertAlmostEqual(flipped.start, -math.pi)
        self.assertEqual(len(join_curves([AtomicLine(P(2, 0, 0), P(2, -3, 0)), ARC], True)), 2)
        merged = join_curves([LINE, PLINE])[0]
        self.assertEqual(merged.points, (P(4, 0, 0), P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(4, 2, 0)))
        square = join_curves([AtomicLine(P(0, 0, 0), P(1, 0, 0)), AtomicLine(P(1, 0, 0), P(1, 1, 0)), AtomicLine(P(1, 1, 0), P(0, 1, 0)), AtomicLine(P(0, 1, 0), P(0, 0, 0))])[0]
        self.assertEqual(square.points[0], P(0, 1, 0))
        self.assertTrue(square.is_closed)

    def test_fillets(self):
        curve, corner = fillet_at(PLINE, 1.7 / 3, 0.5)
        self.assertAlmostEqual(corner, 2 / 3)
        self.assertEqual([type(s).__name__ for s in curve.segments], ["AtomicPolyline", "AtomicArc", "AtomicPolyline"])
        close(self, curve.segments[1].plane.origin, (2.5, 1.5, 0.0))
        self.assertEqual(fillet_at(PLINE, 1 / 3, 3.0), (PLINE, 1 / 3))
        self.assertEqual(fillet_at(PLINE, 1 / 3, 0.0), (PLINE, None))
        seam, _ = fillet_at(CLOSED_PL, 0.0, 0.5)
        self.assertAlmostEqual(seam.start, 0.0625)
        distance = fillet_distance(PLINE, 0.5)
        self.assertEqual([type(s).__name__ for s in distance.segments], ["AtomicLine", "AtomicArc", "AtomicLine", "AtomicArc", "AtomicLine"])
        self.assertEqual(fillet_distance(PLINE, 2.0).spans, (3.0,))  # wrapped, untouched
        self.assertEqual(fillet_distance(PLINE, 0.0), PLINE)
        radius = fillet_radius(PLINE, 3.0)
        self.assertAlmostEqual(radius.segments[1].radius, 1.0)  # clamped to half the shared edge
        with self.assertRaises(ValueError):
            fillet_distance(PLINE, -0.5)

    def test_dash_pattern(self):
        dashes, gaps = dash_pattern(LINE, [1.0, 0.5, 0.25])
        self.assertEqual([(round(d.start.x, 9), round(d.end.x, 9)) for d in dashes], [(0.0, 1.0), (1.5, 1.75), (2.75, 3.25), (3.5, 4.0)])
        self.assertEqual([(round(g.start.x, 9), round(g.end.x, 9)) for g in gaps], [(1.0, 1.5), (1.75, 2.75), (3.25, 3.5)])
        self.assertEqual(dash_pattern(LINE, []), ([], []))
        with self.assertRaises(ValueError):
            dash_pattern(LINE, [1.0, -0.5])

    def test_blends_connect_tangent_curve_and_polyarc(self):
        tangency = blend_curve(LINE_A, LINE_B, 1.0, 1.0, 1)
        close(self, tangency.control_points[1], (4.8284271, 0, 0))
        self.assertAlmostEqual(tangency.knots[-1], 3.8297319, places=6)
        curvature = blend_curve(LINE_A, LINE_B, 0.5, 2.0, 2)
        close(self, curvature.control_points[3], (-0.5254834, 2, 0))
        arc_blend = blend_curve(ARC, AtomicArc(AtomicPlane(P(6, 2, 0), V(0, 0, 1), V(0, -1, 0)), 2.0, AtomicInterval(0.0, math.pi / 2)), 1.0, 1.0, 2)
        close(self, arc_blend.control_points[2], (-5.0596443, -2.0, 0))
        close(self, arc_blend.control_points[3], (0.9403557, 4.0, 0))
        through = blend_curve_through_point(LINE_A, LINE_B, P(3, 1.5, 0), 1)
        self.assertAlmostEqual(through.control_points[1].x, 4.1829, places=3)
        curve, total, domain = tangent_curve([P(0, 0, 0), P(2, 2, 0), P(4, 0, 0)], [V(1, 0, 0)] * 3, 0.5, 5)
        self.assertEqual(len(curve.control_points), 11)
        self.assertAlmostEqual(total, 7.2842706, places=6)
        self.assertEqual(domain.end, total)
        arcs = polyarc([P(0, 0, 0), P(2, 2, 0), P(4, 0, 0), P(6, 2, 0)], V(0, 1, 0), False)
        close(self, arcs.segments[2].plane.origin, (6, 0, 0))
        self.assertAlmostEqual(arcs.segments[2].angle.end, 3 * math.pi / 2)
        self.assertIsInstance(polyarc([P(0, 0, 0), P(2, 2, 0)], None, False), AtomicLine)


if __name__ == "__main__":
    unittest.main()
