"""NURBS kernel guards: recorded evaluation samples plus analytic cross-checks.

The sample golden (``tests/golden/nurbs/samples.json``) freezes curve points,
tangents, lengths, arc-length divisions and surface points produced by the
current kernel so the consolidation into ``Utils/Nurbs`` cannot drift.
The analytic tests do not depend on goldens: a unified circle must evaluate
onto the true circle, and basis functions must sum to one.
"""

from __future__ import annotations

import math
import unittest

from tests.support.golden import UPDATE, golden_path, load_or_record
from tests.support.trees import items_close

from pyhopper import RuledSurface, Sphere
from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicEllipse,
    AtomicInterpolatedCurve,
    AtomicInterval,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicSurface,
)
from pyhopper.Utils.Curves import (
    divide_nurbs_curve_by_distance,
    evaluate_nurbs_curve,
    interpolate_nurbs_curve,
    nurbs_curve_domain,
    nurbs_curve_length,
    nurbs_curve_tangent,
    point_at_normalized_curve_length,
)
from pyhopper.Utils.Nurbs import (
    basis_functions,
    curve_curvature,
    curve_derivatives,
    curve_frame,
    curve_point,
    curve_tangent,
    find_span,
    surface_derivatives,
    surface_normal,
)
from pyhopper.Utils.Surfaces import evaluate_surface
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

GOLDEN = golden_path("nurbs", "samples.json")
PARAMETERS = (0.0, 0.1, 0.25, 0.37, 0.5, 0.66, 0.75, 0.9, 1.0)


def _plane(z: float = 0.0) -> AtomicPlane:
    return AtomicPlane.world_xy(AtomicPoint(0.0, 0.0, z))


def sample_curves() -> dict[str, AtomicNurbsCurve]:
    return {
        "circle": as_nurbs_curve(AtomicCircle(_plane(), 2.0)),
        "arc": as_nurbs_curve(AtomicArc(_plane(), 1.5, AtomicInterval(0.3, 2.4))),
        "ellipse": as_nurbs_curve(AtomicEllipse(_plane(), 3.0, 1.25)),
        "polyline": as_nurbs_curve(AtomicPolyline((AtomicPoint(0, 0, 0), AtomicPoint(2, 1, 0), AtomicPoint(3, 3, 1), AtomicPoint(5, 3, 0)))),
        "interpolated": as_nurbs_curve(AtomicInterpolatedCurve((AtomicPoint(0, 0, 0), AtomicPoint(2, 1.5, 0), AtomicPoint(4, 0, 1), AtomicPoint(6, 2, 0.5)))),
        "global_interpolation": interpolate_nurbs_curve((AtomicPoint(0, 0, 0), AtomicPoint(1, 2, 0), AtomicPoint(3, 2.5, 1), AtomicPoint(4, 0, 0), AtomicPoint(6, 1, 0)), 3),
    }


def sample_surfaces() -> dict[str, AtomicSurface]:
    ruled = RuledSurface(AtomicCircle(_plane(0.0), 2.0), AtomicCircle(_plane(3.0), 3.0)).all_items()[0]
    sphere = Sphere(_plane(0.0), 1.5).all_items()[0]
    return {"ruled": ruled, "sphere": sphere}


def _xyz(point) -> list[float]:
    return [point.x, point.y, point.z]


def _record() -> dict:
    data: dict = {"curves": {}, "surfaces": {}}
    for name, curve in sample_curves().items():
        start, end = nurbs_curve_domain(curve)
        params = [start + (end - start) * t for t in PARAMETERS]
        points, tangents, parameters = divide_nurbs_curve_by_distance(curve, 0.7)
        data["curves"][name] = {
            "domain": [start, end],
            "control_points": [_xyz(p) for p in curve.control_points],
            "weights": list(curve.weights),
            "knots": list(curve.knots),
            "degree": curve.degree,
            "points": [_xyz(evaluate_nurbs_curve(curve, u)) for u in params],
            "tangents": [_xyz(nurbs_curve_tangent(curve, u)) for u in params],
            "length": nurbs_curve_length(curve),
            "arc_length_points": [_xyz(point_at_normalized_curve_length(curve, t)) for t in PARAMETERS],
            "divide_by_0_7": {"points": [_xyz(p) for p in points], "tangents": [_xyz(v) for v in tangents], "parameters": parameters},
        }
    for name, surface in sample_surfaces().items():
        u_knots = surface.u_knots
        v_knots = surface.v_knots
        us = [u_knots[0] + (u_knots[-1] - u_knots[0]) * t for t in PARAMETERS]
        vs = [v_knots[0] + (v_knots[-1] - v_knots[0]) * t for t in (0.0, 0.3, 0.5, 0.8, 1.0)]
        data["surfaces"][name] = {
            "pole_grid": [len(surface.poles), len(surface.poles[0])],
            "degrees": [surface.u_degree, surface.v_degree],
            "points": [[list(evaluate_surface(surface, u, v)) for u in us] for v in vs],
        }
    return data


class NurbsGoldenTests(unittest.TestCase):
    def test_samples_match_golden(self) -> None:
        golden, recorded = load_or_record(GOLDEN, _record)
        if recorded and not UPDATE:
            self.skipTest("golden recorded for the first time")
        current = _record()
        for section in ("curves", "surfaces"):
            for name, expected in golden[section].items():
                with self.subTest(section=section, name=name):
                    self.assertIn(name, current[section])
                    self.assertTrue(
                        items_close(current[section][name], expected, places=9),
                        f"{section}/{name} drifted from the recorded kernel output",
                    )


class NurbsAnalyticTests(unittest.TestCase):
    def test_unified_circle_evaluates_onto_the_circle(self) -> None:
        radius = 2.0
        curve = as_nurbs_curve(AtomicCircle(_plane(), radius))
        start, end = nurbs_curve_domain(curve)
        for t in PARAMETERS:
            point = evaluate_nurbs_curve(curve, start + (end - start) * t)
            self.assertAlmostEqual(math.hypot(point.x, point.y), radius, places=9)
            self.assertAlmostEqual(point.z, 0.0, places=12)
        quarter = evaluate_nurbs_curve(curve, start + (end - start) * 0.25)
        self.assertAlmostEqual(quarter.x, 0.0, places=9)
        self.assertAlmostEqual(quarter.y, radius, places=9)

    def test_circle_tangent_is_perpendicular_to_radius(self) -> None:
        curve = as_nurbs_curve(AtomicCircle(_plane(), 1.0))
        start, end = nurbs_curve_domain(curve)
        for t in (0.1, 0.4, 0.6, 0.9):
            u = start + (end - start) * t
            point = evaluate_nurbs_curve(curve, u)
            tangent = nurbs_curve_tangent(curve, u)
            self.assertAlmostEqual(point.x * tangent.x + point.y * tangent.y, 0.0, places=6)
            self.assertAlmostEqual(math.hypot(tangent.x, tangent.y), 1.0, places=9)

    def test_circle_length_and_arc_length_midpoint(self) -> None:
        curve = as_nurbs_curve(AtomicCircle(_plane(), 2.0))
        self.assertAlmostEqual(nurbs_curve_length(curve), 4.0 * math.pi, places=5)
        half = point_at_normalized_curve_length(curve, 0.5)
        self.assertAlmostEqual(half.x, -2.0, places=5)
        self.assertAlmostEqual(half.y, 0.0, places=5)

    def test_basis_functions_partition_of_unity(self) -> None:
        for curve in sample_curves().values():
            start, end = nurbs_curve_domain(curve)
            for t in (0.05, 0.3, 0.55, 0.95):
                u = start + (end - start) * t
                span = find_span(curve.degree, curve.knots, len(curve.control_points), u)
                self.assertAlmostEqual(sum(basis_functions(span, u, curve.degree, curve.knots)), 1.0, places=12)

    def test_sphere_surface_points_lie_on_sphere(self) -> None:
        sphere = sample_surfaces()["sphere"]
        for u in (0.05, 0.4, 0.7):
            for v in (0.1, 0.5, 0.9):
                x, y, z = evaluate_surface(sphere, u, v)
                self.assertAlmostEqual(math.sqrt(x * x + y * y + z * z), 1.5, places=9)


class NurbsDerivativeTests(unittest.TestCase):
    """Analytic derivatives (K1) against finite differences and closed-form geometry."""

    def test_curve_derivatives_match_central_differences(self) -> None:
        h = 1e-5
        for name, curve in sample_curves().items():
            start, end = nurbs_curve_domain(curve)
            # Stay clear of interior knots: rational arcs are only C1 across their double knots,
            # so a central difference straddling a knot cannot match the one-sided analytic value.
            for t in (0.2, 0.55, 0.8):
                u = start + (end - start) * t
                with self.subTest(curve=name, t=t):
                    point, (first, second) = curve_derivatives(curve, u, 2)
                    before, after = curve_point(curve, u - h), curve_point(curve, u + h)
                    for axis in "xyz":
                        fd1 = (getattr(after, axis) - getattr(before, axis)) / (2 * h)
                        fd2 = (getattr(after, axis) - 2 * getattr(point, axis) + getattr(before, axis)) / (h * h)
                        self.assertAlmostEqual(getattr(first, axis), fd1, places=5)
                        self.assertAlmostEqual(getattr(second, axis), fd2, places=3)

    def test_circle_curvature_is_one_over_radius_and_points_inward(self) -> None:
        curve = as_nurbs_curve(AtomicCircle(_plane(), 2.0))
        for t in (0.0, 0.13, 0.5, 0.77, 1.0):
            point, curvature, vector = curve_curvature(curve, t)
            self.assertAlmostEqual(curvature, 0.5, places=10)
            inward = (-point.x * vector.x - point.y * vector.y) / 2.0
            self.assertAlmostEqual(inward, 0.5, places=10)
            tangent = curve_tangent(curve, t)
            self.assertAlmostEqual(tangent.x * point.x + tangent.y * point.y, 0.0, places=10)

    def test_curve_frame_is_orthonormal_with_tangent_x_axis(self) -> None:
        curve = sample_curves()["global_interpolation"]
        for t in (0.1, 0.45, 0.9):
            frame = curve_frame(curve, t)
            tangent = curve_tangent(curve, t)
            self.assertAlmostEqual(frame.x_axis.x * tangent.x + frame.x_axis.y * tangent.y + frame.x_axis.z * tangent.z, 1.0, places=9)
            self.assertAlmostEqual(frame.normal.x * tangent.x + frame.normal.y * tangent.y + frame.normal.z * tangent.z, 0.0, places=9)
        line = as_nurbs_curve(AtomicPolyline((AtomicPoint(0, 0, 0), AtomicPoint(3, 0, 0))))
        straight = curve_frame(line, 0.5)
        self.assertEqual((straight.x_axis.x, straight.x_axis.y, straight.x_axis.z), (1.0, 0.0, 0.0))

    def test_sphere_normal_is_radial_including_poles(self) -> None:
        sphere = sample_surfaces()["sphere"]
        for u, v in ((0.1, 0.3), (0.6, 0.5), (0.0, 0.0), (0.5, 1.0), (0.25, 0.5)):
            normal = surface_normal(sphere, u, v)
            derivatives = surface_derivatives(sphere, u, v, 1)
            point = derivatives.point
            radius = math.sqrt(point.x ** 2 + point.y ** 2 + point.z ** 2)
            self.assertAlmostEqual((normal.x * point.x + normal.y * point.y + normal.z * point.z) / radius, 1.0, places=9)

    def test_ruled_surface_is_linear_in_v(self) -> None:
        ruled = sample_surfaces()["ruled"]
        derivatives = surface_derivatives(ruled, 0.3, 0.5, 2)
        self.assertEqual((derivatives.dvv.x, derivatives.dvv.y, derivatives.dvv.z), (0.0, 0.0, 0.0))
        self.assertIsNotNone(derivatives.duu)
        first_only = surface_derivatives(ruled, 0.3, 0.5, 1)
        self.assertIsNone(first_only.duu)


if __name__ == "__main__":
    unittest.main()
