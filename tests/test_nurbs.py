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
    _basis_functions,
    _find_span,
    divide_nurbs_curve_by_distance,
    evaluate_nurbs_curve,
    interpolate_nurbs_curve,
    nurbs_curve_domain,
    nurbs_curve_length,
    nurbs_curve_tangent,
    point_at_normalized_curve_length,
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
                span = _find_span(curve, u)
                self.assertAlmostEqual(sum(_basis_functions(curve, span, u)), 1.0, places=12)

    def test_sphere_surface_points_lie_on_sphere(self) -> None:
        sphere = sample_surfaces()["sphere"]
        for u in (0.05, 0.4, 0.7):
            for v in (0.1, 0.5, 0.9):
                x, y, z = evaluate_surface(sphere, u, v)
                self.assertAlmostEqual(math.sqrt(x * x + y * y + z * z), 1.5, places=9)


if __name__ == "__main__":
    unittest.main()
