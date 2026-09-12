"""Curve evaluation utilities for canonical pyhopper curve atoms."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPoint,
    AtomicPolyline,
    AtomicVector,
)
from pyhopper.Utils.Nurbs import (
    basis_row as _basis_row,
    curve_domain,
    curve_point,
    interpolation_knots as _interpolation_knots,
    solve_linear_system as _solve_nurbs_system,
)
from pyhopper.Utils.Vectors import distance as _distance


_TOLERANCE = 1e-12


def nurbs_curve_domain(curve: AtomicNurbsCurve) -> tuple[float, float]:
    """Return the active parameter interval of a valid NURBS curve."""
    return curve_domain(curve)


def evaluate_nurbs_curve(curve: AtomicNurbsCurve, parameter: float) -> AtomicPoint:
    """Evaluate a canonical NURBS curve at one parameter."""
    return curve_point(curve, parameter)


def _interpolation_parameters(
    points: tuple[AtomicPoint, ...],
    knot_style: int,
    periodic: bool,
) -> tuple[float, ...]:
    if knot_style not in (0, 1, 2):
        raise ValueError("Interpolate knot_style must be 0 (uniform), 1 (chord), or 2 (sqrt-chord)")

    segment_count = len(points) if periodic else len(points) - 1
    if knot_style == 0:
        denominator = float(segment_count)
        return tuple(index / denominator for index in range(len(points)))

    exponent = 1.0 if knot_style == 1 else 0.5
    segment_lengths = [
        _distance(points[index], points[(index + 1) % len(points)]) ** exponent
        for index in range(segment_count)
    ]
    total = sum(segment_lengths)
    if total <= _TOLERANCE:
        raise ValueError("Interpolate requires at least two distinct vertices")

    parameters = [0.0]
    for length in segment_lengths[:len(points) - 1]:
        parameters.append(parameters[-1] + length / total)
    return tuple(parameters)


def interpolate_nurbs_curve(
    points: tuple[AtomicPoint, ...],
    degree: int = 3,
    periodic: bool = False,
    knot_style: int = 1,
) -> AtomicNurbsCurve:
    """Build a NURBS curve that passes through every supplied point."""
    if periodic and len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    if len(points) < 2:
        raise ValueError("Interpolate requires at least two vertices")
    if not all(isinstance(point, AtomicPoint) for point in points):
        raise TypeError("Interpolate vertices must all be AtomicPoint values")

    curve_degree = int(degree)
    if curve_degree < 1 or curve_degree % 2 == 0:
        raise ValueError("Interpolate degree must be a positive odd number")
    if curve_degree >= len(points):
        raise ValueError("Interpolate degree must be less than the vertex count")
    parameters = _interpolation_parameters(points, int(knot_style), bool(periodic))
    values = [[point.x, point.y, point.z] for point in points]

    if periodic:
        unique_count = len(points)
        wrapped_count = unique_count + curve_degree
        knots = tuple(
            (index - curve_degree) / unique_count
            for index in range(wrapped_count + curve_degree + 1)
        )
        matrix = []
        for parameter in parameters:
            wrapped_row = _basis_row(parameter, curve_degree, knots, wrapped_count)
            row = [0.0] * unique_count
            for index, value in enumerate(wrapped_row):
                row[index % unique_count] += value
            matrix.append(row)
        solved = _solve_nurbs_system(matrix, values, "Interpolate could not solve the requested curve")
        unique_controls = tuple(AtomicPoint(*coordinates) for coordinates in solved)
        controls = unique_controls + unique_controls[:curve_degree]
    else:
        knots = _interpolation_knots(parameters, curve_degree)
        matrix = [
            _basis_row(parameter, curve_degree, knots, len(points))
            for parameter in parameters
        ]
        controls = tuple(AtomicPoint(*coordinates) for coordinates in _solve_nurbs_system(matrix, values, "Interpolate could not solve the requested curve"))

    return AtomicNurbsCurve(
        control_points=controls,
        weights=tuple(1.0 for _ in controls),
        knots=knots,
        degree=curve_degree,
    )


def _adaptive_span_length(
    curve: AtomicNurbsCurve,
    start: float,
    end: float,
    start_point: AtomicPoint,
    end_point: AtomicPoint,
    tolerance: float,
    depth: int,
) -> float:
    one_third = start + (end - start) / 3.0
    two_thirds = start + 2.0 * (end - start) / 3.0
    point_a = evaluate_nurbs_curve(curve, one_third)
    point_b = evaluate_nurbs_curve(curve, two_thirds)
    chord = _distance(start_point, end_point)
    polygon = (
        _distance(start_point, point_a)
        + _distance(point_a, point_b)
        + _distance(point_b, end_point)
    )
    if depth <= 0 or polygon - chord <= tolerance * max(1.0, polygon):
        return polygon

    return (
        _adaptive_span_length(curve, start, one_third, start_point, point_a, tolerance, depth - 1)
        + _adaptive_span_length(curve, one_third, two_thirds, point_a, point_b, tolerance, depth - 1)
        + _adaptive_span_length(curve, two_thirds, end, point_b, end_point, tolerance, depth - 1)
    )


def nurbs_curve_length(curve: AtomicNurbsCurve, tolerance: float = 1e-7) -> float:
    """Approximate NURBS arc length adaptively over each active knot span."""
    start, end = nurbs_curve_domain(curve)
    boundaries = sorted({start, end, *(knot for knot in curve.knots if start < knot < end)})
    return sum(
        _adaptive_span_length(
            curve,
            span_start,
            span_end,
            evaluate_nurbs_curve(curve, span_start),
            evaluate_nurbs_curve(curve, span_end),
            tolerance,
            10,
        )
        for span_start, span_end in zip(boundaries, boundaries[1:])
        if span_end > span_start
    )


def curve_length(curve, tolerance: float = 1e-7) -> float:
    """Return the length of any supported curve atom."""
    if isinstance(curve, AtomicLine):
        return _distance(curve.start, curve.end)
    if isinstance(curve, AtomicPolyline):
        return sum(_distance(start, end) for start, end in zip(curve.points, curve.points[1:]))
    if isinstance(curve, AtomicCircle):
        return 2.0 * math.pi * abs(float(curve.radius))
    if isinstance(curve, AtomicArc):
        return abs(float(curve.angle.length) * float(curve.radius))

    from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

    return nurbs_curve_length(as_nurbs_curve(curve), tolerance)


def point_at_normalized_curve_length(
    curve: AtomicNurbsCurve,
    normalized_length: float,
    tolerance: float = 1e-7,
) -> AtomicPoint:
    """Evaluate a NURBS curve at a normalized arc-length factor.

    ``0.0`` returns the curve start and ``1.0`` returns the curve end. Values
    outside that range are clamped so authored sliders cannot evaluate outside
    the curve.
    """
    factor = min(1.0, max(0.0, float(normalized_length)))
    start, end = nurbs_curve_domain(curve)
    if factor <= 0.0:
        return evaluate_nurbs_curve(curve, start)
    if factor >= 1.0:
        return evaluate_nurbs_curve(curve, end)

    boundaries = sorted({start, end, *(knot for knot in curve.knots if start < knot < end)})
    samples: list[tuple[float, AtomicPoint]] = []
    for span_start, span_end in zip(boundaries, boundaries[1:]):
        span_samples = _adaptive_span_samples(
            curve,
            span_start,
            span_end,
            evaluate_nurbs_curve(curve, span_start),
            evaluate_nurbs_curve(curve, span_end),
            tolerance,
            10,
        )
        samples.extend(span_samples if not samples else span_samples[1:])

    cumulative = [0.0]
    for (_, point_a), (_, point_b) in zip(samples, samples[1:]):
        cumulative.append(cumulative[-1] + _distance(point_a, point_b))

    total = cumulative[-1]
    if total <= _TOLERANCE:
        raise ValueError("Point On Curve requires a non-zero-length curve")

    target = total * factor
    sample_index = 1
    while sample_index < len(cumulative) - 1 and cumulative[sample_index] < target:
        sample_index += 1

    lower = sample_index - 1
    segment_length = cumulative[sample_index] - cumulative[lower]
    local = 0.0 if segment_length <= _TOLERANCE else (target - cumulative[lower]) / segment_length
    parameter = samples[lower][0] + (samples[sample_index][0] - samples[lower][0]) * local
    return evaluate_nurbs_curve(curve, parameter)


def nurbs_curve_tangent(curve: AtomicNurbsCurve, parameter: float) -> AtomicVector:
    """Return a unit tangent using a stable local finite difference."""
    start, end = nurbs_curve_domain(curve)
    span = max(abs(end - start), 1.0)
    epsilon = span * 1e-7
    before = max(start, float(parameter) - epsilon)
    after = min(end, float(parameter) + epsilon)
    if after <= before:
        raise ValueError("Cannot evaluate tangent on a zero-length curve domain")
    point_before = evaluate_nurbs_curve(curve, before)
    point_after = evaluate_nurbs_curve(curve, after)
    tangent = AtomicVector(
        point_after.x - point_before.x,
        point_after.y - point_before.y,
        point_after.z - point_before.z,
    ).unitize()
    if tangent.length == 0.0:
        raise ValueError("Cannot evaluate tangent at a stationary curve point")
    return tangent


def _adaptive_span_samples(
    curve: AtomicNurbsCurve,
    start: float,
    end: float,
    start_point: AtomicPoint,
    end_point: AtomicPoint,
    tolerance: float,
    depth: int,
) -> list[tuple[float, AtomicPoint]]:
    one_third = start + (end - start) / 3.0
    two_thirds = start + 2.0 * (end - start) / 3.0
    point_a = evaluate_nurbs_curve(curve, one_third)
    point_b = evaluate_nurbs_curve(curve, two_thirds)
    chord = _distance(start_point, end_point)
    polygon = _distance(start_point, point_a) + _distance(point_a, point_b) + _distance(point_b, end_point)
    if depth <= 0 or polygon - chord <= tolerance * max(1.0, polygon):
        return [(start, start_point), (one_third, point_a), (two_thirds, point_b), (end, end_point)]

    samples = []
    segments = (
        (start, one_third, start_point, point_a),
        (one_third, two_thirds, point_a, point_b),
        (two_thirds, end, point_b, end_point),
    )
    for segment_start, segment_end, segment_start_point, segment_end_point in segments:
        segment_samples = _adaptive_span_samples(
            curve,
            segment_start,
            segment_end,
            segment_start_point,
            segment_end_point,
            tolerance,
            depth - 1,
        )
        samples.extend(segment_samples if not samples else segment_samples[1:])
    return samples


def divide_nurbs_curve_by_distance(
    curve: AtomicNurbsCurve,
    distance: float,
    tolerance: float = 1e-7,
) -> tuple[list[AtomicPoint], list[AtomicVector], list[float]]:
    """Divide a NURBS curve at fixed arc-length intervals."""
    interval = float(distance)
    if interval <= 0.0:
        raise ValueError("Divide Distance requires a distance greater than zero")

    start, end = nurbs_curve_domain(curve)
    boundaries = sorted({start, end, *(knot for knot in curve.knots if start < knot < end)})
    samples: list[tuple[float, AtomicPoint]] = []
    for span_start, span_end in zip(boundaries, boundaries[1:]):
        span_samples = _adaptive_span_samples(
            curve,
            span_start,
            span_end,
            evaluate_nurbs_curve(curve, span_start),
            evaluate_nurbs_curve(curve, span_end),
            tolerance,
            10,
        )
        samples.extend(span_samples if not samples else span_samples[1:])

    cumulative = [0.0]
    for (_, point_a), (_, point_b) in zip(samples, samples[1:]):
        cumulative.append(cumulative[-1] + _distance(point_a, point_b))
    total = cumulative[-1]
    if total <= _TOLERANCE:
        raise ValueError("Divide Distance requires a non-zero-length curve")

    target_count = int(math.floor((total + tolerance) / interval))
    targets = [index * interval for index in range(target_count + 1)]
    closed = _distance(samples[0][1], samples[-1][1]) <= tolerance * max(1.0, total)
    if closed and targets and abs(targets[-1] - total) <= tolerance * max(1.0, total):
        targets.pop()

    parameters = []
    sample_index = 1
    for target in targets:
        while sample_index < len(cumulative) - 1 and cumulative[sample_index] < target:
            sample_index += 1
        lower = sample_index - 1
        segment_length = cumulative[sample_index] - cumulative[lower]
        local = 0.0 if segment_length <= _TOLERANCE else (target - cumulative[lower]) / segment_length
        parameter = samples[lower][0] + (samples[sample_index][0] - samples[lower][0]) * local
        parameters.append(parameter)

    points = [evaluate_nurbs_curve(curve, parameter) for parameter in parameters]
    tangents = [nurbs_curve_tangent(curve, parameter) for parameter in parameters]
    return points, tangents, parameters


# ── Reparametrization ───────────────────────────────────────────────


def reparametrize_nurbs_curve(curve: AtomicNurbsCurve) -> AtomicNurbsCurve:
    """Return the same curve with its parameter domain mapped affinely onto [0, 1].

    The geometry is untouched; only the knot vector is rescaled, so a point
    evaluated at ``t`` on the result equals the point at ``start + t * (end - start)``
    on the input.
    """
    start, end = nurbs_curve_domain(curve)
    span = end - start
    if abs(span) <= _TOLERANCE:
        raise ValueError("Cannot reparametrize a NURBS curve with a zero-length domain")
    knots = tuple((float(knot) - start) / span for knot in curve.knots)
    return AtomicNurbsCurve(
        control_points=curve.control_points,
        weights=curve.weights,
        knots=knots,
        degree=curve.degree,
    )


def reparametrize_curve(item):
    """Reparametrize a curve atom to [0, 1]; non-NURBS items pass through unchanged.

    Named curve atoms (lines, circles, arcs, polylines, …) already unify to a
    [0, 1] domain, so only explicit ``AtomicNurbsCurve`` values need rescaling.
    """
    if isinstance(item, AtomicNurbsCurve):
        return reparametrize_nurbs_curve(item)
    return item


def reparametrize_tree(tree):
    """Apply :func:`reparametrize_curve` to every item of a DataTree, preserving paths."""
    from pyhopper.Core.DataTree import DataTree

    source = DataTree.coerce(tree)
    return DataTree.from_branches({path: [reparametrize_curve(item) for item in branch] for path, branch in source.branches()})
