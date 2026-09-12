"""Shared vector / plane / NURBS helper modules."""

from __future__ import annotations

import math
import unittest

from pyhopper.Core.Atoms import AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Utils import Nurbs, Planes, Vectors

# Captured from RhinoCommon Vector3d.PerpendicularTo (Rhino 8.35, headless) on 2026-09-11.
PERPENDICULAR_ORACLE = [
    ((0, 0, 1), (1.0, 0.0, -0.0)),
    ((1, 0, 0), (-0.0, 1.0, 0.0)),
    ((0, 1, 0), (0.0, -0.0, 1.0)),
    ((0, 0, -1), (-1.0, 0.0, -0.0)),
    ((-1, 0, 0), (-0.0, -1.0, 0.0)),
    ((0, -1, 0), (0.0, -0.0, -1.0)),
    ((1, 1, 0), (-0.7071067811865475, 0.7071067811865475, 0.0)),
    ((1, 0, 1), (-0.7071067811865475, 0.0, 0.7071067811865475)),
    ((0, 1, 1), (0.0, -0.7071067811865475, 0.7071067811865475)),
    ((1, 2, 3), (0.0, 0.8320502943378436, -0.554700196225229)),
    ((3, -2, 1), (0.554700196225229, 0.8320502943378436, 0.0)),
    ((-2, 5, -4), (0.0, 0.6246950475544243, 0.7808688094430304)),
    ((0.3, 0.1, -0.9), (-0.9486832980505138, 0.0, -0.3162277660168379)),
    ((2, 2, 2), (-0.7071067811865475, 0.7071067811865475, 0.0)),
    ((0.001, 5, 0.001), (0.0, -0.0001999999960000001, 0.9999999800000006)),
]


class VectorTests(unittest.TestCase):
    def test_perpendicular_matches_opennurbs(self):
        for raw, expected in PERPENDICULAR_ORACLE:
            with self.subTest(vector=raw):
                result = Vectors.perpendicular(AtomicVector(*raw))
                for got, want in zip((result.x, result.y, result.z), expected):
                    self.assertAlmostEqual(got, want, places=12)
                self.assertAlmostEqual(Vectors.dot(result, AtomicVector(*raw)), 0.0, places=12)

    def test_perpendicular_of_zero_vector_is_zero(self):
        self.assertEqual(Vectors.perpendicular(AtomicVector(0, 0, 0)), AtomicVector(0.0, 0.0, 0.0))

    def test_algebra_types(self):
        p, v = AtomicPoint(1, 2, 3), AtomicVector(1, 0, 0)
        self.assertIsInstance(Vectors.add(p, v), AtomicPoint)
        self.assertIsInstance(Vectors.add(v, v), AtomicVector)
        self.assertIsInstance(Vectors.sub(p, p), AtomicVector)
        self.assertEqual(Vectors.cross(AtomicVector(1, 0, 0), AtomicVector(0, 1, 0)), AtomicVector(0.0, 0.0, 1.0))
        self.assertAlmostEqual(Vectors.angle(AtomicVector(1, 0, 0), AtomicVector(0, 1, 0)), math.pi / 2)
        self.assertEqual(Vectors.lerp(AtomicPoint(0, 0, 0), AtomicPoint(2, 4, 6), 0.5), AtomicPoint(1.0, 2.0, 3.0))
        self.assertEqual(Vectors.unit(AtomicVector(0, 0, 0)), AtomicVector(0.0, 0.0, 0.0))


class PlaneTests(unittest.TestCase):
    def test_plane_coordinates_round_trip(self):
        plane = AtomicPlane(AtomicPoint(1, 2, 3), AtomicVector(0, 0, 1), AtomicVector(1, 1, 0))
        point = Planes.point_on_plane(plane, 2.0, -1.5, 0.5)
        x, y, z = Planes.plane_coordinates(plane, point)
        self.assertAlmostEqual(x, 2.0)
        self.assertAlmostEqual(y, -1.5)
        self.assertAlmostEqual(z, 0.5)
        self.assertAlmostEqual(Planes.signed_distance(plane, point), 0.5)
        projected = Planes.project_point(plane, point)
        self.assertAlmostEqual(Planes.signed_distance(plane, projected), 0.0)

    def test_plane_from_normal_uses_rhino_x_axis(self):
        plane = Planes.plane_from_normal(AtomicPoint(0, 0, 0), AtomicVector(0, 0, 2))
        self.assertEqual(plane.x_axis, AtomicVector(1.0, 0.0, 0.0))
        yz = Planes.plane_from_normal(AtomicPoint(0, 0, 0), AtomicVector(1, 0, 0))
        self.assertEqual(yz.x_axis, AtomicVector(0.0, 1.0, 0.0))
        with self.assertRaises(ValueError):
            Planes.plane_from_normal(AtomicPoint(0, 0, 0), AtomicVector(0, 0, 0))


class NurbsModuleTests(unittest.TestCase):
    def test_knot_round_trips(self):
        knots, mults = (0.0, 0.5, 1.0), (3, 1, 3)
        full = Nurbs.expand_knots(knots, mults)
        self.assertEqual(full, (0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0))
        self.assertEqual(Nurbs.collapse_knots(full), (knots, mults))
        self.assertEqual(Nurbs.rhino_knots(full), (0.0, 0.0, 0.5, 1.0, 1.0))
        self.assertEqual(Nurbs.from_rhino_knots(Nurbs.rhino_knots(full)), full)

    def test_curve_profile_accepts_full_or_unique_knots(self):
        line = AtomicNurbsCurve((AtomicPoint(0, 0, 0), AtomicPoint(1, 0, 0)), (1.0, 1.0), (0.0, 0.0, 1.0, 1.0), 1)
        profile = Nurbs.curve_profile(line, "Test")
        self.assertEqual((profile.knots, profile.mults, profile.degree), ((0.0, 1.0), (2, 2), 1))
        with self.assertRaises(ValueError):
            Nurbs.curve_profile(AtomicNurbsCurve((AtomicPoint(0, 0, 0),), (1.0,), (), 1), "Test")

    def test_greville_abscissae(self):
        full = (0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0)  # 4 poles, degree 2
        self.assertEqual(Nurbs.greville_abscissae(full, 2, 4), [0.0, 0.25, 0.75, 1.0])


if __name__ == "__main__":
    unittest.main()
