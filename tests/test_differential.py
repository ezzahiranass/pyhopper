"""Differential geometry kernel behind the K1 analysis components.

The expected numbers were read off Grasshopper 8 with the probes recorded while
building the wave (rhino-test/oracle/cases/{Curve,Surface}/*.json hold the full
comparisons); the derivative checks pin the analytic native-atom derivatives to
central differences of the evaluated points.
"""

from __future__ import annotations

import math
import unittest

from pyhopper.Core.Atoms import AtomicArc, AtomicCircle, AtomicInterval, AtomicLine, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicPolyline, AtomicSurface
from pyhopper.Utils.Curves import curve_derivatives_at, curve_point_at
from pyhopper.Utils.Differential import curvature_circle, curve_analysis, discontinuities, frenet_frame, offset_surface, osculating_circle, surface_analysis, torsion

P = AtomicPoint


def nurbs(points, degree=3, knots=None):
    count = len(points)
    if knots is None:
        knots = [0.0] * (degree + 1) + [i / (count - degree) for i in range(1, count - degree)] + [1.0] * (degree + 1)
    return AtomicNurbsCurve(tuple(P(*p) for p in points), (1.0,) * count, tuple(float(k) for k in knots), degree)


def surface(rows, u_degree, v_degree):
    return AtomicSurface(poles=tuple(tuple(P(*p) for p in row) for row in rows), weights=tuple((1.0,) * len(row) for row in rows),
                         u_knots=(0.0, 1.0), v_knots=(0.0, 1.0), u_mults=(u_degree + 1, u_degree + 1), v_mults=(v_degree + 1, v_degree + 1),
                         u_degree=u_degree, v_degree=v_degree)


CUBIC = nurbs([(0, 0, 0), (1, 2, 0), (3, 2, 1), (4, 0, 0)])
TWISTED = nurbs([(0, 0, 0), (1, 2, 1), (3, 2, 2), (4, 0, 3), (6, 1, 4)])
CIRCLE = AtomicCircle(AtomicPlane.world_xy(), 2.0)
ARC = AtomicArc(AtomicPlane.world_xy(), 2.0, AtomicInterval(0.0, math.pi / 2))
LINE = AtomicLine(P(0, 0, 0), P(4, 0, 0))
POLYLINE = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(4, 2, 0)))
DOME = surface([[(0, 0, 0), (2, 0, 1), (4, 0, 0)], [(0, 2, 1), (2, 2, 3), (4, 2, 1)], [(0, 4, 0), (2, 4, 1), (4, 4, 0)]], 2, 2)
SADDLE = surface([[(0, 0, 0), (2, 0, 1), (4, 0, 0)], [(0, 2, -1), (2, 2, 0), (4, 2, -1)], [(0, 4, 0), (2, 4, 1), (4, 4, 0)]], 2, 2)
CYLINDER = surface([[(0, 0, 0), (2, 0, 1), (4, 0, 0)], [(0, 2, 0), (2, 2, 1), (4, 2, 0)]], 2, 1)


def close(test, actual, expected, places=4):
    for a, e in zip((actual.x, actual.y, actual.z), expected):
        test.assertAlmostEqual(a, e, places=places)


class CurveDerivativeTests(unittest.TestCase):
    def test_native_atoms_match_central_differences(self):
        step = 1e-6
        for curve, t in ((LINE, 0.25), (POLYLINE, 0.5), (POLYLINE, 0.1), (CIRCLE, 0.125), (ARC, 0.3), (CUBIC, 0.3)):
            with self.subTest(curve=type(curve).__name__, t=t):
                point, first, second, _ = curve_derivatives_at(curve, t)
                close(self, point, tuple(getattr(curve_point_at(curve, t), axis) for axis in "xyz"), places=9)
                before, after = curve_point_at(curve, t - step), curve_point_at(curve, t + step)
                close(self, first, ((after.x - before.x) / (2 * step), (after.y - before.y) / (2 * step), (after.z - before.z) / (2 * step)), places=4)
                if isinstance(curve, (AtomicCircle, AtomicArc)):
                    centre = curve.plane.origin
                    speed = math.sqrt(first.x ** 2 + first.y ** 2 + first.z ** 2)
                    # second derivative points at the centre with |r'|² / r
                    close(self, second, ((centre.x - point.x) * speed ** 2 / 4.0, (centre.y - point.y) * speed ** 2 / 4.0, 0.0), places=6)

    def test_curvature_matches_grasshopper(self):
        analysis = curve_analysis(CUBIC, 0.3)
        close(self, analysis.curvature_vector, (0.2201, -0.4125, 0.0528))
        circle = curvature_circle(analysis)
        close(self, circle.plane.origin, (2.1102, -0.6032, 0.4277))
        self.assertAlmostEqual(circle.radius, 2.1253, places=4)
        # the plane's x axis points from the centre back to the curve point
        close(self, circle.plane.x_axis, ((analysis.point.x - circle.plane.origin.x) / circle.radius, (analysis.point.y - circle.plane.origin.y) / circle.radius, (analysis.point.z - circle.plane.origin.z) / circle.radius))

    def test_straight_stretches_get_a_200_long_tangent_line(self):
        line = curvature_circle(curve_analysis(LINE, 0.25))
        self.assertIsInstance(line, AtomicLine)
        close(self, line.start, (-99.0, 0.0, 0.0), places=9)
        close(self, line.end, (101.0, 0.0, 0.0), places=9)
        self.assertEqual(curve_analysis(POLYLINE, 0.5).curvature, 0.0)

    def test_torsion(self):
        self.assertAlmostEqual(torsion(curve_analysis(CUBIC, 0.3)), 0.2531653581182219, places=9)
        self.assertAlmostEqual(torsion(curve_analysis(TWISTED, 0.6)), -5.4824561403508705, places=9)
        self.assertEqual(torsion(curve_analysis(LINE, 0.5)), 0.0)
        self.assertAlmostEqual(torsion(curve_analysis(CIRCLE, 0.3)), 0.0, places=9)

    def test_frames_use_the_openNURBS_perpendicular_on_straights(self):
        frame = frenet_frame(curve_analysis(LINE, 0.5))
        close(self, frame.x_axis, (1, 0, 0))
        close(self, frame.normal, (0, 0, 1))
        vertical = frenet_frame(curve_analysis(AtomicLine(P(0, 0, 0), P(0, 0, 4)), 0.5))
        close(self, vertical.x_axis, (0, 0, 1))
        close(self, vertical.normal, (0, 1, 0))
        along_y = frenet_frame(curve_analysis(AtomicLine(P(0, 0, 0), P(0, 4, 0)), 0.5))
        close(self, along_y.normal, (1, 0, 0))
        circle = frenet_frame(curve_analysis(CIRCLE, 0.125))
        close(self, circle.normal, (0, 0, 1))
        close(self, circle.x_axis, (-math.sqrt(0.5), math.sqrt(0.5), 0))


class DiscontinuityTests(unittest.TestCase):
    def test_levels(self):
        multi = nurbs([(0, 0, 0), (1, 2, 0), (2, 2, 0), (3, 0, 0), (4, 0, 0), (5, 2, 0), (6, 2, 0)])
        self.assertEqual(discontinuities(multi, 1)[1], [0.0, 1.0])
        self.assertEqual(discontinuities(multi, 2)[1], [0.0, 1.0])
        self.assertEqual(discontinuities(multi, 3)[1], [0.0, 0.25, 0.5, 0.75, 1.0])
        kinked = nurbs([(0, 0, 0), (1, 2, 0), (2, 2, 0), (3, 0, 0), (4, 0, 0), (5, 2, 0), (6, 2, 0)], 3, [0, 0, 0, 0, 0.5, 0.5, 0.5, 1, 1, 1, 1])
        self.assertEqual(discontinuities(kinked, 1)[1], [0.0, 0.5, 1.0])
        with self.assertRaises(ValueError):
            discontinuities(multi, 0)

    def test_polylines_and_smooth_atoms(self):
        self.assertEqual(discontinuities(POLYLINE, 1)[1], [0.0, 1 / 3, 2 / 3, 1.0])
        collinear = AtomicPolyline((P(0, 0, 0), P(1, 0, 0), P(3, 0, 0), P(3, 2, 0)))
        self.assertEqual(discontinuities(collinear, 1)[1], [0.0, 2 / 3, 1.0])
        self.assertEqual(discontinuities(collinear, 3)[1], [0.0, 1 / 3, 2 / 3, 1.0])
        closed = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(0, 2, 0), P(0, 0, 0)))
        self.assertEqual(discontinuities(closed, 1)[1], [0.0, 0.25, 0.5, 0.75])
        self.assertEqual(discontinuities(CIRCLE, 1)[1], [])
        self.assertEqual(discontinuities(ARC, 1)[1], [0.0, 1.0])
        self.assertEqual(discontinuities(LINE, 1)[1], [0.0, 1.0])


class SurfaceAnalysisTests(unittest.TestCase):
    def test_curvatures_match_grasshopper(self):
        dome = surface_analysis(DOME, 0.5, 0.5)
        self.assertAlmostEqual(dome.gaussian, 0.140625, places=9)
        self.assertAlmostEqual(dome.mean, -0.375, places=9)
        close(self, dome.normal, (0, 0, 1))
        corner = surface_analysis(DOME, 0.0, 0.0)
        self.assertAlmostEqual(corner.gaussian, 0.0, places=9)
        self.assertAlmostEqual(corner.mean, -0.2041241452319315, places=9)
        close(self, corner.frame.normal, (-0.408248, -0.408248, 0.816497), places=5)
        close(self, corner.frame.x_axis, (0.894427, 0.0, 0.447214), places=5)
        saddle = surface_analysis(SADDLE, 0.5, 0.5)
        self.assertAlmostEqual(saddle.gaussian, -0.0625, places=9)
        self.assertAlmostEqual(saddle.maximum, 0.25, places=9)
        self.assertAlmostEqual(saddle.minimum, -0.25, places=9)

    def test_principal_ordering_prefers_the_larger_absolute_curvature(self):
        cylinder = surface_analysis(CYLINDER, 0.5, 0.5)
        self.assertAlmostEqual(cylinder.maximum, -0.25, places=9)
        self.assertAlmostEqual(cylinder.minimum, 0.0, places=9)
        self.assertAlmostEqual(abs(cylinder.max_direction.x), 1.0, places=9)
        self.assertAlmostEqual(abs(cylinder.min_direction.y), 1.0, places=9)

    def test_osculating_circles(self):
        cylinder = surface_analysis(CYLINDER, 0.5, 0.5)
        circle = osculating_circle(cylinder, cylinder.maximum, cylinder.max_direction)
        close(self, circle.plane.origin, (2.0, 1.0, -3.5), places=9)
        self.assertAlmostEqual(circle.radius, 4.0, places=9)
        line = osculating_circle(cylinder, cylinder.minimum, cylinder.min_direction)
        self.assertIsInstance(line, AtomicLine)
        self.assertAlmostEqual(math.dist((line.start.x, line.start.y, line.start.z), (line.end.x, line.end.y, line.end.z)), 10.0, places=9)
        dome = surface_analysis(DOME, 0.25, 0.6)
        first = osculating_circle(dome, dome.maximum, dome.max_direction)
        close(self, first.plane.origin, (1.99279, 2.03106, -1.64822), places=4)
        self.assertAlmostEqual(first.radius, 2.884689, places=5)

    def test_degenerate_normal_raises(self):
        pinched = surface([[(0, 0, 0), (0, 0, 0)], [(0, 2, 0), (4, 2, 0)]], 1, 1)
        with self.assertRaises(ValueError):
            surface_analysis(pinched, 0.5, 0.0)

    def test_offset_translates_planar_surfaces_exactly(self):
        flat = surface([[(0, 0, 0), (4, 0, 0)], [(0, 2, 0), (4, 2, 0)]], 1, 1)
        offset = offset_surface(flat, 1.5)
        self.assertEqual([[(p.x, p.y, p.z) for p in row] for row in offset.poles], [[(0.0, 0.0, 1.5), (4.0, 0.0, 1.5)], [(0.0, 2.0, 1.5), (4.0, 2.0, 1.5)]])
        dome = offset_surface(DOME, 0.5)
        centre = surface_analysis(dome, 0.5, 0.5)
        self.assertAlmostEqual(centre.point.z, surface_analysis(DOME, 0.5, 0.5).point.z + 0.5, places=6)


if __name__ == "__main__":
    unittest.main()
