"""Curve kernel vs RhinoCommon: points, tangents, derivatives, length, equal-length division."""

from __future__ import annotations

import math
import unittest

from oracle.support import assert_close, assert_parallel, load, requires_rhino, to_nurbs_curve

from pyhopper.Utils.Curves import divide_nurbs_curve_by_count, nurbs_curve_domain, nurbs_curve_length
from pyhopper.Utils.Nurbs import curve_curvature, curve_derivatives, curve_point, curve_tangent

PARAMETERS = (0.0, 0.1, 0.27, 0.5, 0.66, 0.83, 1.0)


def _sample_curves():
    from tests.test_nurbs import sample_curves

    return sample_curves()


@requires_rhino
class CurveOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.Rhino = load()
        cls.curves = _sample_curves()

    def _pairs(self):
        for name, curve in self.curves.items():
            rhino_curve = to_nurbs_curve(curve)
            self.assertTrue(rhino_curve.IsValid, f"{name}: RhinoCommon rejected the converted curve")
            yield name, curve, rhino_curve

    def test_domains_agree(self) -> None:
        for name, curve, rhino_curve in self._pairs():
            with self.subTest(curve=name):
                start, end = nurbs_curve_domain(curve)
                self.assertAlmostEqual(rhino_curve.Domain.T0, start, places=12)
                self.assertAlmostEqual(rhino_curve.Domain.T1, end, places=12)

    def test_points_and_tangents(self) -> None:
        for name, curve, rhino_curve in self._pairs():
            start, end = nurbs_curve_domain(curve)
            for t in PARAMETERS:
                u = start + (end - start) * t
                with self.subTest(curve=name, t=t):
                    assert_close(self, curve_point(curve, u), rhino_curve.PointAt(u), 1e-9, "point")
                    assert_close(self, curve_tangent(curve, u), rhino_curve.TangentAt(u), 1e-7, "tangent")

    def test_first_and_second_derivatives(self) -> None:
        for name, curve, rhino_curve in self._pairs():
            start, end = nurbs_curve_domain(curve)
            for t in (0.15, 0.4, 0.62, 0.9):  # away from the double knots of rational arcs
                u = start + (end - start) * t
                with self.subTest(curve=name, t=t):
                    point, (first, second) = curve_derivatives(curve, u, 2)
                    rhino_ders = rhino_curve.DerivativeAt(u, 2)
                    assert_close(self, point, rhino_ders[0], 1e-9, "point")
                    assert_close(self, first, rhino_ders[1], 1e-6, "first derivative")
                    assert_close(self, second, rhino_ders[2], 1e-5, "second derivative")

    def test_curvature(self) -> None:
        for name, curve, rhino_curve in self._pairs():
            start, end = nurbs_curve_domain(curve)
            for t in (0.15, 0.4, 0.62, 0.9):
                u = start + (end - start) * t
                with self.subTest(curve=name, t=t):
                    _, curvature, vector = curve_curvature(curve, u)
                    rhino_vector = rhino_curve.CurvatureAt(u)
                    self.assertAlmostEqual(curvature, rhino_vector.Length, places=6)
                    if rhino_vector.Length > 1e-6:
                        assert_close(self, vector, rhino_vector, 1e-6, "curvature vector")

    def test_length(self) -> None:
        for name, curve, rhino_curve in self._pairs():
            with self.subTest(curve=name):
                self.assertAlmostEqual(nurbs_curve_length(curve), rhino_curve.GetLength(), delta=1e-6 * max(1.0, rhino_curve.GetLength()))

    def test_divide_by_count_matches_rhino_parameters(self) -> None:
        for name, curve, rhino_curve in self._pairs():
            with self.subTest(curve=name):
                points, tangents, parameters = divide_nurbs_curve_by_count(curve, 7)
                rhino_parameters = list(rhino_curve.DivideByCount(7, True))
                if rhino_curve.IsClosed:
                    rhino_parameters = rhino_parameters[:7]
                self.assertEqual(len(parameters), len(rhino_parameters))
                for ours, theirs in zip(parameters, rhino_parameters):
                    self.assertAlmostEqual(ours, theirs, delta=1e-6)
                for point, u in zip(points, rhino_parameters):
                    assert_close(self, point, rhino_curve.PointAt(u), 1e-5, "division point")
                for tangent, u in zip(tangents, rhino_parameters):
                    assert_parallel(self, tangent, rhino_curve.TangentAt(u), 1e-6, "division tangent")


if __name__ == "__main__":
    unittest.main()
