"""Closest-point kernel behind the K3 wave (curves, surfaces, rays, sides, extremes).

The expected numbers were read off Grasshopper 8 with the probes recorded while
building the wave (rhino-test/oracle/cases/{Vector,Curve,Surface}/*.json hold
the full comparisons).
"""

from __future__ import annotations

import math
import unittest

from pyhopper.Core.Atoms import AtomicArc, AtomicBrep, AtomicCircle, AtomicInterval, AtomicLine, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicPolyline, AtomicSurface, AtomicTrimmedSurface, AtomicVector
from pyhopper.Utils.ClosestPoints import (
    brep_closest_point,
    curve_closest_point,
    curve_curve_closest,
    curve_extremes,
    curve_geometry_closest,
    curve_side,
    geometry_ray_hit,
    point_in_closed_curve,
    surface_closest_point,
    surface_line_hits,
    uv_in_trim,
)
from pyhopper.Utils.CurvesOnSurfaces import offset_on_surface, project_curve, pull_curve

P, V = AtomicPoint, AtomicVector


def nurbs(points, degree=3):
    count = len(points)
    knots = [0.0] * (degree + 1) + [i / (count - degree) for i in range(1, count - degree)] + [1.0] * (degree + 1)
    return AtomicNurbsCurve(tuple(P(*p) for p in points), (1.0,) * count, tuple(knots), degree)


def surface(rows, u_degree, v_degree):
    return AtomicSurface(poles=tuple(tuple(P(*p) for p in row) for row in rows), weights=tuple((1.0,) * len(row) for row in rows),
                         u_knots=(0.0, 1.0), v_knots=(0.0, 1.0), u_mults=(u_degree + 1, u_degree + 1), v_mults=(v_degree + 1, v_degree + 1),
                         u_degree=u_degree, v_degree=v_degree)


CUBIC = nurbs([(0, 0, 0), (1, 2, 0), (3, 2, 1), (4, 0, 0)])
CIRCLE = AtomicCircle(AtomicPlane.world_xy(), 2.0)
LINE = AtomicLine(P(0, 0, 0), P(4, 0, 0))
PLINE = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(4, 2, 0)))
CLOSED = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(0, 2, 0), P(0, 0, 0)))
ARC = AtomicArc(AtomicPlane.world_xy(), 2.0, AtomicInterval(0.0, math.pi / 2))
DOME = surface([[(0, 0, 0), (2, 0, 1), (4, 0, 0)], [(0, 2, 1), (2, 2, 3), (4, 2, 1)], [(0, 4, 0), (2, 4, 1), (4, 4, 0)]], 2, 2)
FLAT = surface([[(0, 0, 0), (4, 0, 0)], [(0, 2, 0), (4, 2, 0)]], 1, 1)


def close(test, actual, expected, places=5):
    for a, e in zip((actual.x, actual.y, actual.z), expected):
        test.assertAlmostEqual(a, e, places=places)


class CurveClosestPointTests(unittest.TestCase):
    def test_matches_grasshopper(self):
        t, p, d = curve_closest_point(CUBIC, P(2, 3, 0))
        self.assertAlmostEqual(t, 0.49254760469475467, places=9)
        close(self, p, (1.966465, 1.499667, 0.369329))
        self.assertAlmostEqual(d, 1.54548634231662, places=9)
        t, p, d = curve_closest_point(CIRCLE, P(3, 1, 0))
        self.assertAlmostEqual(t * 4 * math.pi, 0.6435011087932844, places=9)  # Rhino's arc-length parameter
        close(self, p, (1.897367, 0.632456, 0.0))
        self.assertEqual(curve_closest_point(CIRCLE, P(0, 0, 0))[0], 0.0)  # axis point: the seam
        self.assertAlmostEqual(curve_closest_point(CIRCLE, P(-3, 0, 0))[0], 0.5)
        self.assertEqual(curve_closest_point(LINE, P(5, 1, 0))[:1], (1.0,))
        self.assertAlmostEqual(curve_closest_point(PLINE, P(3, -1, 0))[0], 1 / 3)
        self.assertAlmostEqual(curve_closest_point(ARC, P(-1, -1, 0))[0], 1.0)  # opposite the middle: Rhino lands on the end

    def test_proximity(self):
        _, _, a, b, d = curve_curve_closest(LINE, AtomicLine(P(1, -1, 1), P(1, 1, 1)))
        close(self, a, (1, 0, 0))
        close(self, b, (1, 0, 1))
        self.assertAlmostEqual(d, 1.0)
        _, _, a, b, d = curve_curve_closest(CUBIC, AtomicCircle(AtomicPlane(P(2, 5, 0), V(0, 0, 1), V(1, 0, 0)), 1.0))
        close(self, a, (1.971202, 1.499754, 0.370140))
        close(self, b, (1.991773, 4.000034, 0.0))
        self.assertAlmostEqual(d, 2.5276124015344656, places=6)
        a, b, d = curve_geometry_closest(CUBIC, CIRCLE)
        close(self, a, (1.367935, 1.379486, 0.247118))
        close(self, b, (1.408255, 1.420147, 0.0))
        a, b, d = curve_geometry_closest(AtomicLine(P(0, 2, 2), P(4, 2, 2)), DOME)
        close(self, b, (2, 2, 1.25))

    def test_side(self):
        self.assertEqual(curve_side(CUBIC, P(2, 3, 0), None), -1)
        self.assertEqual(curve_side(CUBIC, P(2, -3, 0), None), 1)
        self.assertEqual(curve_side(LINE, P(2, 0, 0), None), 0)
        self.assertEqual(curve_side(LINE, P(2, 1, 0), AtomicPlane(P(0, 0, 0), V(0, 0, -1), V(1, 0, 0))), 1)
        xz = AtomicCircle(AtomicPlane(P(0, 0, 0), V(0, 1, 0), V(1, 0, 0)), 2.0)
        xz_flipped = AtomicCircle(AtomicPlane(P(0, 0, 0), V(0, -1, 0), V(1, 0, 0)), 2.0)
        self.assertEqual((curve_side(xz, P(0, 0, 0), None), curve_side(xz_flipped, P(0, 0, 0), None)), (-1, -1))
        self.assertEqual(curve_side(CLOSED, P(1, 1, 0), None), -1)
        self.assertEqual(curve_side(AtomicPolyline(tuple(reversed(CLOSED.points))), P(1, 1, 0), None), 1)
        self.assertEqual(curve_side(AtomicLine(P(0, 0, 0), P(0, 0, 4)), P(1, 0, 2), None), 0)

    def test_point_in_curve(self):
        self.assertEqual(point_in_closed_curve(CIRCLE, P(0.5, 0.5, 0))[0], 2)
        self.assertEqual(point_in_closed_curve(CIRCLE, P(3, 0, 0))[0], 0)
        self.assertEqual(point_in_closed_curve(CIRCLE, P(2.005, 0, 0))[0], 1)
        self.assertEqual(point_in_closed_curve(CIRCLE, P(2.02, 0, 0))[0], 0)
        relationship, projected = point_in_closed_curve(CIRCLE, P(0.5, 0.5, 1))
        self.assertEqual((relationship, projected), (2, P(0.5, 0.5, 0.0)))
        self.assertEqual(point_in_closed_curve(CLOSED, P(2, 2, 0))[0], 1)
        with self.assertRaises(ValueError):
            point_in_closed_curve(CUBIC, P(0.5, 0.5, 0))

    def test_extremes(self):
        highest, lowest = curve_extremes(CUBIC, AtomicPlane.world_xy())
        close(self, highest, (2.740741, 1.333333, 0.444444))
        close(self, lowest, (0, 0, 0))
        highest, lowest = curve_extremes(CUBIC, AtomicPlane(P(0, 0, 0), V(-1, 0, 0), V(0, 1, 0)))
        close(self, highest, (0, 0, 0))
        close(self, lowest, (4, 0, 0))
        highest, lowest = curve_extremes(ARC, AtomicPlane(P(0, 0, 0), V(0, 1, 0), V(1, 0, 0)))
        close(self, highest, (0, 2, 0))
        close(self, lowest, (2, 0, 0))


class SurfaceClosestPointTests(unittest.TestCase):
    def test_matches_grasshopper(self):
        u, v, p, d, clamped = surface_closest_point(DOME, P(1, 3, 2))
        self.assertAlmostEqual(u, 0.3135802713017384, places=6)
        self.assertAlmostEqual(v, 0.6864197286982617, places=6)
        close(self, p, (1.254321, 2.745679, 1.046317))
        self.assertAlmostEqual(d, 1.0192495715507683, places=6)
        self.assertFalse(clamped)
        u, v, p, d, clamped = surface_closest_point(DOME, P(2, -3, 0))
        self.assertEqual((round(u, 9), round(v, 9)), (0.5, 0.0))
        close(self, p, (2, 0, 0.5))
        self.assertTrue(clamped)
        self.assertEqual(surface_closest_point(DOME, P(6, 6, 0))[:2], (1.0, 1.0))
        point, normal, d = brep_closest_point(AtomicBrep((DOME,)), P(1, 3, 2))
        close(self, normal, (-0.249518, 0.249518, 0.935672))
        self.assertAlmostEqual(d, 1.0192495715507683, places=6)

    def test_rays(self):
        hits = surface_line_hits(DOME, P(1, 1, 5), V(0, 0, -1))
        self.assertEqual(len(hits), 1)
        close(self, hits[0][3], (1, 1, 0.890625), 9)
        close(self, surface_line_hits(DOME, P(0, 0, 5), V(1, 1, -2))[0][3], (1.877798, 1.877798, 1.244404))
        self.assertEqual(surface_line_hits(DOME, P(10, 10, 5), V(0, 0, -1)), [])
        self.assertIsNone(geometry_ray_hit(DOME, P(1, 1, 5), V(0, 0, 1)))  # behind the point
        s, on_ray = geometry_ray_hit(LINE, P(2, 0.0005, 5), V(0, 0, -1))
        close(self, on_ray, (2, 0.0005, 0), 9)
        self.assertIsNone(geometry_ray_hit(LINE, P(2, 0.1, 5), V(0, 0, -1)))

    def test_trims(self):
        self.assertTrue(uv_in_trim(DOME, 0.5, 0.5))
        self.assertFalse(uv_in_trim(DOME, 1.5, 0.5))
        self.assertTrue(uv_in_trim(DOME, 1.0, 0.5))
        outer = AtomicPolyline((P(0.1, 0.1, 0), P(0.9, 0.1, 0), P(0.9, 0.9, 0), P(0.1, 0.9, 0), P(0.1, 0.1, 0)))
        hole = AtomicPolyline((P(0.4, 0.4, 0), P(0.6, 0.4, 0), P(0.6, 0.6, 0), P(0.4, 0.6, 0), P(0.4, 0.4, 0)))
        trimmed = AtomicTrimmedSurface(FLAT, outer, (hole,))
        self.assertTrue(uv_in_trim(trimmed, 0.2, 0.2))
        self.assertFalse(uv_in_trim(trimmed, 0.5, 0.5))
        self.assertFalse(uv_in_trim(trimmed, 0.05, 0.5))


class CurvesOnSurfacesTests(unittest.TestCase):
    def test_pull_project_and_offset(self):
        pulled = pull_curve(AtomicLine(P(0.5, 0.5, 5), P(3.5, 3.5, 5)), DOME)
        self.assertEqual(len(pulled), 1)
        close(self, pulled[0].control_points[0], (1.378293, 1.378293, 1.107389), 4)
        self.assertEqual(pull_curve(AtomicLine(P(5, 0.5, 5), P(8, 1.5, 5)), FLAT), [])
        self.assertEqual(pull_curve(ARC, FLAT), [ARC])
        self.assertEqual(pull_curve(AtomicLine(P(2, -1, 5), P(2, 3, 5)), FLAT)[0], AtomicLine(P(2, 0, 0), P(2, 2, 0)))
        projected = project_curve(AtomicLine(P(-1, 2, 5), P(5, 2, 5)), AtomicBrep((DOME,)), V(0, 0, 1))
        self.assertEqual(len(projected), 1)
        close(self, projected[0].control_points[0], (0, 2, 0.5), 5)
        close(self, projected[0].control_points[-1], (4, 2, 0.5), 5)
        offset = offset_on_surface(AtomicPolyline((P(0.5, 0.5, 0), P(2, 0.5, 0), P(2, 1.5, 0))), 0.25, FLAT)
        self.assertEqual(offset[0].points, (P(0.5, 0.75, 0.0), P(1.75, 0.75, 0.0), P(1.75, 1.5, 0.0)))
        self.assertEqual(offset_on_surface(AtomicLine(P(0.5, 0.5, 0), P(3.5, 0.5, 0)), -0.25, FLAT)[0].points, (P(0.5, 0.25, 0.0), P(3.5, 0.25, 0.0)))


if __name__ == "__main__":
    unittest.main()
