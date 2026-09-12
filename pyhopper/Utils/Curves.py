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


_TOLERANCE = 1e-12


def _find_span(curve: AtomicNurbsCurve, parameter: float) -> int:
    degree = curve.degree
    knots = curve.knots
    control_point_count = len(curve.control_points)

    if parameter >= knots[control_point_count]:
        return control_point_count - 1
    if parameter <= knots[degree]:
        return degree

    low = degree
    high = control_point_count
    span = (low + high) // 2
    while parameter < knots[span] or parameter >= knots[span + 1]:
        if parameter < knots[span]:
            high = span
        else:
            low = span
        span = (low + high) // 2
    return span


def _basis_functions(curve: AtomicNurbsCurve, span: int, parameter: float) -> list[float]:
    degree = curve.degree
    knots = curve.knots
    basis = [0.0] * (degree + 1)
    basis[0] = 1.0
    left = [0.0] * (degree + 1)
    right = [0.0] * (degree + 1)

    for index in range(1, degree + 1):
        left[index] = parameter - knots[span + 1 - index]
        right[index] = knots[span + index] - parameter
        saved = 0.0
        for basis_index in range(index):
            denominator = right[basis_index + 1] + left[index - basis_index]
            term = 0.0 if abs(denominator) < 1e-12 else basis[basis_index] / denominator
            basis[basis_index] = saved + right[basis_index + 1] * term
            saved = left[index - basis_index] * term
        basis[index] = saved

    return basis


def nurbs_curve_domain(curve: AtomicNurbsCurve) -> tuple[float, float]:
    """Return the active parameter interval of a valid NURBS curve."""
    point_count = len(curve.control_points)
    degree = int(curve.degree)
    if point_count < 2 or degree < 1 or degree >= point_count:
        raise ValueError("NURBS curve has an invalid control-point count or degree")
    if len(curve.knots) != point_count + degree + 1:
        raise ValueError("NURBS curve knot count must equal point count + degree + 1")
    return float(curve.knots[degree]), float(curve.knots[point_count])


def evaluate_nurbs_curve(curve: AtomicNurbsCurve, parameter: float) -> AtomicPoint:
    """Evaluate a canonical NURBS curve at one parameter."""
    start, end = nurbs_curve_domain(curve)
    value = min(end, max(start, float(parameter)))
    span = _find_span(curve, value)
    basis = _basis_functions(curve, span, value)
    weights = (
        curve.weights
        if len(curve.weights) == len(curve.control_points)
        else tuple(1.0 for _ in curve.control_points)
    )
    x = y = z = total_weight = 0.0

    for local_index, basis_value in enumerate(basis):
        control_index = span - curve.degree + local_index
        point = curve.control_points[control_index]
        coefficient = basis_value * weights[control_index]
        x += coefficient * point.x
        y += coefficient * point.y
        z += coefficient * point.z
        total_weight += coefficient

    if abs(total_weight) < 1e-12:
        raise ValueError("NURBS curve evaluation produced a zero rational weight")
    return AtomicPoint(x / total_weight, y / total_weight, z / total_weight)


def _distance(a: AtomicPoint, b: AtomicPoint) -> float:
    return math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2 + (b.z - a.z) ** 2)


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


def _interpolation_knots(parameters: tuple[float, ...], degree: int) -> tuple[float, ...]:
    interior = tuple(
        sum(parameters[index:index + degree]) / degree
        for index in range(1, len(parameters) - degree)
    )
    return (0.0,) * (degree + 1) + interior + (1.0,) * (degree + 1)


def _basis_row(
    parameter: float,
    degree: int,
    knots: tuple[float, ...],
    control_point_count: int,
) -> list[float]:
    if parameter >= knots[control_point_count]:
        span = control_point_count - 1
    else:
        low = degree
        high = control_point_count
        span = (low + high) // 2
        while parameter < knots[span] or parameter >= knots[span + 1]:
            if parameter < knots[span]:
                high = span
            else:
                low = span
            span = (low + high) // 2

    basis = [0.0] * (degree + 1)
    basis[0] = 1.0
    left = [0.0] * (degree + 1)
    right = [0.0] * (degree + 1)
    for order in range(1, degree + 1):
        left[order] = parameter - knots[span + 1 - order]
        right[order] = knots[span + order] - parameter
        saved = 0.0
        for index in range(order):
            denominator = right[index + 1] + left[order - index]
            term = 0.0 if abs(denominator) <= _TOLERANCE else basis[index] / denominator
            basis[index] = saved + right[index + 1] * term
            saved = left[order - index] * term
        basis[order] = saved

    row = [0.0] * control_point_count
    for local_index, value in enumerate(basis):
        row[span - degree + local_index] = value
    return row


def _solve_linear_system(matrix: list[list[float]], values: list[list[float]]) -> list[list[float]]:
    size = len(matrix)
    augmented = [matrix[row][:] + values[row][:] for row in range(size)]
    value_count = len(values[0])
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= _TOLERANCE:
            raise ValueError("Interpolate could not solve the requested curve")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if abs(factor) <= _TOLERANCE:
                continue
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column])
            ]
    return [row[size:size + value_count] for row in augmented]


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
        solved = _solve_linear_system(matrix, values)
        unique_controls = tuple(AtomicPoint(*coordinates) for coordinates in solved)
        controls = unique_controls + unique_controls[:curve_degree]
    else:
        knots = _interpolation_knots(parameters, curve_degree)
        matrix = [
            _basis_row(parameter, curve_degree, knots, len(points))
            for parameter in parameters
        ]
        controls = tuple(AtomicPoint(*coordinates) for coordinates in _solve_linear_system(matrix, values))

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
