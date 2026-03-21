"""Type unifiers for converting atoms into compatible canonical forms."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
)


def _expand_knots(unique_knots: tuple[float, ...], mults: tuple[int, ...]) -> tuple[float, ...]:
    expanded = []
    for knot, mult in zip(unique_knots, mults):
        expanded.extend([float(knot)] * int(mult))
    return tuple(expanded)


def _open_uniform_bspline_data(point_count: int, degree: int) -> tuple[tuple[float, ...], tuple[int, ...], int]:
    if point_count < 2:
        raise ValueError("A spline requires at least two control points")

    clamped_degree = max(1, min(int(degree), point_count - 1))
    knot_count = point_count - clamped_degree + 1

    if knot_count == 2:
        return (0.0, 1.0), (clamped_degree + 1, clamped_degree + 1), clamped_degree

    denominator = float(knot_count - 1)
    knots = tuple(index / denominator for index in range(knot_count))
    mults = tuple(
        clamped_degree + 1 if index in (0, knot_count - 1) else 1
        for index in range(knot_count)
    )
    return knots, mults, clamped_degree


def _point_on_plane(plane: AtomicPlane, x: float, y: float) -> AtomicPoint:
    y_axis = plane.y_axis
    return AtomicPoint(
        plane.origin.x + x * plane.x_axis.x + y * y_axis.x,
        plane.origin.y + x * plane.x_axis.y + y * y_axis.y,
        plane.origin.z + x * plane.x_axis.z + y * y_axis.z,
    )


def _arc_like_to_nurbs(plane: AtomicPlane, radius: float, start_angle: float, end_angle: float) -> AtomicNurbsCurve:
    sweep = end_angle - start_angle
    if sweep == 0.0:
        raise ValueError("Cannot convert a zero-length arc to a NURBS curve")

    segment_count = max(1, int(math.ceil(abs(sweep) / (math.pi / 2.0))))
    delta = sweep / segment_count

    control_points = []
    weights = []

    for index in range(segment_count):
        angle_a = start_angle + index * delta
        angle_b = angle_a + delta
        angle_mid = (angle_a + angle_b) / 2.0
        half_delta = delta / 2.0
        mid_weight = math.cos(half_delta)
        if abs(mid_weight) < 1e-12:
            raise ValueError("Arc span is too large to convert to a quadratic NURBS segment")

        start_point = _point_on_plane(
            plane,
            radius * math.cos(angle_a),
            radius * math.sin(angle_a),
        )
        middle_point = _point_on_plane(
            plane,
            (radius / mid_weight) * math.cos(angle_mid),
            (radius / mid_weight) * math.sin(angle_mid),
        )
        end_point = _point_on_plane(
            plane,
            radius * math.cos(angle_b),
            radius * math.sin(angle_b),
        )

        if index == 0:
            control_points.append(start_point)
            weights.append(1.0)

        control_points.append(middle_point)
        weights.append(mid_weight)
        control_points.append(end_point)
        weights.append(1.0)

    unique_knots = tuple(index / segment_count for index in range(segment_count + 1))
    multiplicities = tuple(
        3 if index in (0, segment_count) else 2
        for index in range(segment_count + 1)
    )

    return AtomicNurbsCurve(
        control_points=tuple(control_points),
        weights=tuple(weights),
        knots=_expand_knots(unique_knots, multiplicities),
        degree=2,
    )


def as_nurbs_curve(curve) -> AtomicNurbsCurve:
    """Convert supported curve atoms into a canonical ``AtomicNurbsCurve``."""
    if isinstance(curve, AtomicNurbsCurve):
        weights = curve.weights if len(curve.weights) == len(curve.control_points) else tuple(
            1.0 for _ in curve.control_points
        )
        if curve.knots:
            return AtomicNurbsCurve(
                control_points=curve.control_points,
                weights=weights,
                knots=tuple(float(knot) for knot in curve.knots),
                degree=curve.degree,
            )

        unique_knots, mults, degree = _open_uniform_bspline_data(len(curve.control_points), curve.degree)
        return AtomicNurbsCurve(
            control_points=curve.control_points,
            weights=weights,
            knots=_expand_knots(unique_knots, mults),
            degree=degree,
        )

    if isinstance(curve, AtomicLine):
        return AtomicNurbsCurve(
            control_points=(curve.start, curve.end),
            weights=(1.0, 1.0),
            knots=(0.0, 0.0, 1.0, 1.0),
            degree=1,
        )

    if isinstance(curve, AtomicPolyline):
        if len(curve.points) < 2:
            raise ValueError("Polyline must contain at least two points")
        unique_knots, mults, degree = _open_uniform_bspline_data(len(curve.points), 1)
        return AtomicNurbsCurve(
            control_points=curve.points,
            weights=tuple(1.0 for _ in curve.points),
            knots=_expand_knots(unique_knots, mults),
            degree=degree,
        )

    if isinstance(curve, AtomicCircle):
        return _arc_like_to_nurbs(curve.plane, curve.radius, 0.0, 2.0 * math.pi)

    if isinstance(curve, AtomicArc):
        return _arc_like_to_nurbs(curve.plane, curve.radius, curve.angle.start, curve.angle.end)

    raise TypeError(f"Cannot unify curve type {type(curve).__name__} to AtomicNurbsCurve")
