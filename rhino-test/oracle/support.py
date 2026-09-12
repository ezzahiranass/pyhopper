"""Rhino 8 oracle support: boot Rhino.Inside once and convert atoms to/from RhinoCommon.

Run with the rhino-test virtualenv (pythonnet + rhinoinside):

    rhino-test\\.venv\\Scripts\\python -m unittest discover -s rhino-test/oracle -v

Every test module is skipped when Rhino 8 or ``rhinoinside`` is unavailable,
so this suite never runs as part of the default ``tests/`` discovery.
"""

from __future__ import annotations

import importlib.util
import math
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RHINO_SYSTEM = Path(os.environ.get("RHINO_SYSTEM_DIR", r"C:\Program Files\Rhino 8\System"))
_FRAMEWORK = os.environ.get("RHINO_INSIDE_FRAMEWORK", "net8.0")
_rhino = None


def rhino_available() -> bool:
    return importlib.util.find_spec("rhinoinside") is not None and RHINO_SYSTEM.exists()


requires_rhino = unittest.skipUnless(rhino_available(), "Rhino 8 + rhinoinside not available")


def load():
    """Boot RhinoCore headless once per process and return the ``Rhino`` namespace."""
    global _rhino
    if _rhino is not None:
        return _rhino
    import rhinoinside

    rhinoinside.load(str(RHINO_SYSTEM), _FRAMEWORK)
    import clr  # noqa: F401  (pythonnet)

    clr.AddReference("RhinoCommon")
    import Rhino  # type: ignore

    _rhino = Rhino
    return Rhino


# ── Atom → RhinoCommon ──────────────────────────────────────────────


def to_point(point):
    return load().Geometry.Point3d(float(point.x), float(point.y), float(point.z))


def to_vector(vector):
    return load().Geometry.Vector3d(float(vector.x), float(vector.y), float(vector.z))


def to_plane(plane):
    return load().Geometry.Plane(to_point(plane.origin), to_vector(plane.x_axis), to_vector(plane.y_axis))


def to_line(line):
    return load().Geometry.Line(to_point(line.start), to_point(line.end))


def to_circle(circle):
    return load().Geometry.Circle(to_plane(circle.plane), float(circle.radius))


def to_arc(arc):
    Rhino = load()
    circle = Rhino.Geometry.Circle(to_plane(arc.plane), float(arc.radius))
    return Rhino.Geometry.Arc(circle, Rhino.Geometry.Interval(float(arc.angle.start), float(arc.angle.end)))


def to_polyline(polyline):
    Rhino = load()
    result = Rhino.Geometry.Polyline()
    for point in polyline.points:
        result.Add(float(point.x), float(point.y), float(point.z))
    return result


def to_nurbs_curve(curve):
    """AtomicNurbsCurve (full knot vector) → RhinoCommon NurbsCurve (Rhino knot convention)."""
    Rhino = load()
    count = len(curve.control_points)
    degree = int(curve.degree)
    weights = curve.weights if len(curve.weights) == count else tuple(1.0 for _ in curve.control_points)
    result = Rhino.Geometry.NurbsCurve(3, True, degree + 1, count)
    for index, (point, weight) in enumerate(zip(curve.control_points, weights)):
        # The (Point3d, weight) overload takes Euclidean coordinates; the 4-double overload is homogeneous.
        result.Points.SetPoint(index, Rhino.Geometry.Point3d(float(point.x), float(point.y), float(point.z)), float(weight))
    rhino_knots = curve.knots[1:-1]  # Rhino drops the superfluous first and last knot
    for index, knot in enumerate(rhino_knots):
        result.Knots[index] = float(knot)
    return result


def to_nurbs_surface(surface):
    """AtomicSurface (poles[v][u], unique knots + mults) → RhinoCommon NurbsSurface."""
    Rhino = load()
    from pyhopper.Utils.Nurbs import expanded_surface_knots, surface_degrees

    v_count = len(surface.poles)
    u_count = len(surface.poles[0])
    u_degree, v_degree = surface_degrees(surface)
    u_knots, v_knots = expanded_surface_knots(surface)
    result = Rhino.Geometry.NurbsSurface.Create(3, True, u_degree + 1, v_degree + 1, u_count, v_count)
    for v_index, row in enumerate(surface.poles):
        for u_index, point in enumerate(row):
            weight = float(surface.weights[v_index][u_index])
            result.Points.SetPoint(u_index, v_index, Rhino.Geometry.Point3d(float(point.x), float(point.y), float(point.z)), weight)
    for index, knot in enumerate(u_knots[1:-1]):
        result.KnotsU[index] = float(knot)
    for index, knot in enumerate(v_knots[1:-1]):
        result.KnotsV[index] = float(knot)
    return result


def to_transform(transform):
    Rhino = load()
    result = Rhino.Geometry.Transform(0.0)
    m = transform.matrix
    for row in range(4):
        for col in range(4):
            setattr(result, f"M{row}{col}", float(m[row * 4 + col]))
    return result


# ── Comparisons ─────────────────────────────────────────────────────


def xyz(value) -> tuple[float, float, float]:
    """Coordinates of a pyhopper atom or a RhinoCommon point/vector."""
    if hasattr(value, "X"):
        return float(value.X), float(value.Y), float(value.Z)
    return float(value.x), float(value.y), float(value.z)


def assert_close(testcase: unittest.TestCase, actual, expected, tolerance: float = 1e-6, message: str = "") -> None:
    a, b = xyz(actual), xyz(expected)
    if math.dist(a, b) > tolerance:
        testcase.fail(f"{message + ': ' if message else ''}{a} != {b} (|d| = {math.dist(a, b):.3e} > {tolerance})")


def assert_parallel(testcase: unittest.TestCase, actual, expected, tolerance: float = 1e-6, message: str = "") -> None:
    """Directions equal up to sign."""
    a, b = xyz(actual), xyz(expected)
    dot = abs(sum(x * y for x, y in zip(a, b)))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))
    if norm == 0.0 or abs(dot / norm - 1.0) > tolerance:
        testcase.fail(f"{message + ': ' if message else ''}{a} not parallel to {b}")
