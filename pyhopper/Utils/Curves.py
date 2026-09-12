"""Curve evaluation utilities for canonical pyhopper curve atoms."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicEllipse,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyCurve,
    AtomicPolyline,
    AtomicRectangle,
    AtomicVector,
)
from pyhopper.Utils.Nurbs import (
    basis_row as _basis_row,
    curve_domain,
    curve_point,
    curve_tangent,
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


# 7-point Gauss-Legendre rule on [-1, 1]
_GAUSS_NODES = (0.0, 0.4058451513773972, -0.4058451513773972, 0.7415311855993945, -0.7415311855993945, 0.9491079123427585, -0.9491079123427585)
_GAUSS_WEIGHTS = (0.4179591836734694, 0.3818300505051189, 0.3818300505051189, 0.2797053914892766, 0.2797053914892766, 0.1294849661688697, 0.1294849661688697)


def _speed(curve: AtomicNurbsCurve, parameter: float) -> float:
    from pyhopper.Utils.Nurbs import curve_derivatives

    _, (first,) = curve_derivatives(curve, parameter, 1)
    return math.sqrt(first.x * first.x + first.y * first.y + first.z * first.z)


def _gauss_length(curve: AtomicNurbsCurve, start: float, end: float) -> float:
    middle, half = 0.5 * (start + end), 0.5 * (end - start)
    return half * sum(weight * _speed(curve, middle + half * node) for node, weight in zip(_GAUSS_NODES, _GAUSS_WEIGHTS))


def _adaptive_length(curve: AtomicNurbsCurve, start: float, end: float, whole: float, tolerance: float, depth: int, boundaries: list[float] | None) -> float:
    """Arc length of ``[start, end]`` by adaptive Gauss-Legendre quadrature of the speed: the span is
    bisected until the two half estimates agree with the whole one (cusps and reversals, where the
    speed is not smooth, are isolated by the bisection). ``boundaries`` collects the leaf interval ends."""
    middle = 0.5 * (start + end)
    left, right = _gauss_length(curve, start, middle), _gauss_length(curve, middle, end)
    if depth <= 0 or abs(left + right - whole) <= tolerance * max(1.0, left + right):
        if boundaries is not None:
            boundaries.append(middle)
            boundaries.append(end)
        return left + right
    return _adaptive_length(curve, start, middle, left, tolerance, depth - 1, boundaries) + _adaptive_length(curve, middle, end, right, tolerance, depth - 1, boundaries)


def _span_boundaries(curve: AtomicNurbsCurve) -> list[float]:
    start, end = nurbs_curve_domain(curve)
    return sorted({start, end, *(float(knot) for knot in curve.knots if start < knot < end)})


def nurbs_curve_length(curve: AtomicNurbsCurve, tolerance: float = 1e-7) -> float:
    """NURBS arc length: adaptive Gauss-Legendre quadrature of the speed over every knot span."""
    boundaries = _span_boundaries(curve)
    return sum(
        _adaptive_length(curve, span_start, span_end, _gauss_length(curve, span_start, span_end), tolerance * 1e-3, 24, None)
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
    if isinstance(curve, AtomicPolyCurve):
        return sum(curve_length(segment, tolerance) for segment in curve.segments)

    from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

    return nurbs_curve_length(as_nurbs_curve(curve), tolerance)


class _LengthTable:
    """Cumulative arc length at the adaptive quadrature boundaries of a NURBS curve, with exact
    (quadrature) refinement inside a bracket for both length -> parameter and parameter -> length."""

    def __init__(self, curve: AtomicNurbsCurve, tolerance: float) -> None:
        self.curve = curve
        self.parameters: list[float] = []
        self.cumulative: list[float] = []
        boundaries = _span_boundaries(curve)
        self.parameters.append(boundaries[0])
        self.cumulative.append(0.0)
        for span_start, span_end in zip(boundaries, boundaries[1:]):
            if span_end <= span_start:
                continue
            leaves: list[float] = []
            _adaptive_length(curve, span_start, span_end, _gauss_length(curve, span_start, span_end), tolerance * 1e-3, 24, leaves)
            previous = span_start
            for leaf in sorted(set(leaves)):
                if leaf <= previous:
                    continue
                self.cumulative.append(self.cumulative[-1] + _gauss_length(curve, previous, leaf))
                self.parameters.append(leaf)
                previous = leaf

    @property
    def total(self) -> float:
        return self.cumulative[-1]

    def length_at(self, parameter: float) -> float:
        t = float(parameter)
        if t <= self.parameters[0]:
            return 0.0
        if t >= self.parameters[-1]:
            return self.total
        index = 1
        while index < len(self.parameters) - 1 and self.parameters[index] < t:
            index += 1
        lower = index - 1
        return self.cumulative[lower] + _gauss_length(self.curve, self.parameters[lower], t)

    def parameter_at(self, length: float) -> float:
        target = min(self.total, max(0.0, float(length)))
        if target <= 0.0:
            return self.parameters[0]
        if target >= self.total:
            return self.parameters[-1]
        index = 1
        while index < len(self.cumulative) - 1 and self.cumulative[index] < target:
            index += 1
        lower = index - 1
        origin, low, high = self.parameters[lower], self.parameters[lower], self.parameters[index]
        base = self.cumulative[lower]
        # Newton on the monotone length function, guarded by the bracket
        t = low + (high - low) * (target - base) / max(self.cumulative[index] - base, _TOLERANCE)
        for _ in range(60):
            residual = base + _gauss_length(self.curve, origin, t) - target
            if abs(residual) <= 1e-13 * max(1.0, self.total):
                break
            if residual > 0:
                high = t
            else:
                low = t
            speed = _speed(self.curve, t)
            step = t - residual / speed if speed > _TOLERANCE else 0.5 * (low + high)
            t = step if low < step < high else 0.5 * (low + high)
            if high - low <= 1e-15 * max(1.0, abs(high)):
                break
        return t


def _arc_length_table(curve: AtomicNurbsCurve, tolerance: float = 1e-7) -> _LengthTable:
    return _LengthTable(curve, tolerance)


def _parameter_at_length(table: _LengthTable, cumulative, target: float) -> float:
    return table.parameter_at(target)


def parameter_at_normalized_curve_length(
    curve: AtomicNurbsCurve,
    normalized_length: float,
    tolerance: float = 1e-7,
) -> float:
    """Parameter at a normalized arc-length factor (0 = start, 1 = end, clamped)."""
    factor = min(1.0, max(0.0, float(normalized_length)))
    start, end = nurbs_curve_domain(curve)
    if factor <= 0.0:
        return start
    if factor >= 1.0:
        return end
    table = _arc_length_table(curve, tolerance)
    if table.total <= _TOLERANCE:
        raise ValueError("Point On Curve requires a non-zero-length curve")
    return table.parameter_at(table.total * factor)


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
    return evaluate_nurbs_curve(curve, parameter_at_normalized_curve_length(curve, normalized_length, tolerance))


def is_closed_nurbs_curve(curve: AtomicNurbsCurve, tolerance: float = 1e-9) -> bool:
    """True when the curve start and end coincide (relative to the curve size)."""
    start, end = nurbs_curve_domain(curve)
    first = evaluate_nurbs_curve(curve, start)
    last = evaluate_nurbs_curve(curve, end)
    extent = max(1.0, *(abs(coordinate) for point in curve.control_points for coordinate in (point.x, point.y, point.z)))
    return _distance(first, last) <= tolerance * extent


def divide_nurbs_curve_by_count(
    curve: AtomicNurbsCurve,
    count: int,
    tolerance: float = 1e-7,
) -> tuple[list[AtomicPoint], list[AtomicVector], list[float]]:
    """Divide a curve into *count* equal arc-length segments (Grasshopper Divide Curve).

    Open curves yield ``count + 1`` division points; closed curves yield
    ``count`` (the seam point is not repeated).
    """
    segments = int(count)
    if segments < 1:
        raise ValueError("Divide Curve requires at least one segment")
    table = _arc_length_table(curve, tolerance)
    total = table.total
    if total <= _TOLERANCE:
        raise ValueError("Divide Curve requires a non-zero-length curve")
    start, end = nurbs_curve_domain(curve)
    closed = is_closed_nurbs_curve(curve)
    point_count = segments if closed else segments + 1
    parameters: list[float] = []
    for index in range(point_count):
        if index == 0:
            parameters.append(start)
        elif index == segments:
            parameters.append(end)
        else:
            parameters.append(table.parameter_at(total * index / segments))
    points = [evaluate_nurbs_curve(curve, parameter) for parameter in parameters]
    tangents = [nurbs_curve_tangent(curve, parameter) for parameter in parameters]
    return points, tangents, parameters


def nurbs_curve_tangent(curve: AtomicNurbsCurve, parameter: float) -> AtomicVector:
    """Return the unit tangent at *parameter* (analytic first derivative)."""
    return curve_tangent(curve, parameter)


def divide_nurbs_curve_by_distance(
    curve: AtomicNurbsCurve,
    distance: float,
    tolerance: float = 1e-7,
) -> tuple[list[AtomicPoint], list[AtomicVector], list[float]]:
    """Divide a NURBS curve at fixed arc-length intervals."""
    interval = float(distance)
    if interval <= 0.0:
        raise ValueError("Divide Distance requires a distance greater than zero")
    table = _arc_length_table(curve, tolerance)
    total = table.total
    if total <= _TOLERANCE:
        raise ValueError("Divide Distance requires a non-zero-length curve")

    target_count = int(math.floor((total + tolerance) / interval))
    targets = [index * interval for index in range(target_count + 1)]
    if is_closed_nurbs_curve(curve) and targets and abs(targets[-1] - total) <= tolerance * max(1.0, total):
        targets.pop()
    parameters = [table.parameter_at(target) for target in targets]
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
    [0, 1] domain, so only ``AtomicNurbsCurve`` values (knot domain) and
    ``AtomicPolyCurve`` values (segment spans) need rescaling.
    """
    if isinstance(item, AtomicNurbsCurve):
        return reparametrize_nurbs_curve(item)
    if isinstance(item, AtomicPolyCurve):
        spans = polycurve_spans(item)
        total = sum(spans)
        if total <= _TOLERANCE:
            raise ValueError("Cannot reparametrize a polycurve with a zero-length domain")
        return AtomicPolyCurve(item.segments, tuple(span / total for span in spans), 0.0)
    return item


def reparametrize_tree(tree):
    """Apply :func:`reparametrize_curve` to every item of a DataTree, preserving paths."""
    from pyhopper.Core.DataTree import DataTree

    source = DataTree.coerce(tree)
    return DataTree.from_branches({path: [reparametrize_curve(item) for item in branch] for path, branch in source.branches()})


# ── Atom-aware parameterisation ─────────────────────────────────────
#
# Grasshopper evaluates each curve type with its own parameterisation: lines
# by length, polylines uniformly per segment, arcs and circles by angle (their
# Rhino parameter is arc length), NURBS by knots. pyhopper keeps those
# semantics but normalises every non-NURBS atom to the domain [0, 1] — exactly
# what a Grasshopper curve param with "Reparameterize" produces — so a
# parameter means the same thing on both sides. Verified with the headless
# oracle (rhino-test/oracle).

_NATIVE_ATOMS = (AtomicLine, AtomicPolyline, AtomicArc, AtomicCircle)


def _as_nurbs(curve) -> AtomicNurbsCurve:
    if isinstance(curve, AtomicNurbsCurve):
        return curve
    from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

    return as_nurbs_curve(curve)


def natural_span(curve) -> float:
    """The parameter length Rhino gives a curve of this kind: a line's length, an arc's length, a
    polyline's segment count, a NURBS curve's knot domain (2π for ellipses, 4 for rectangles)."""
    if isinstance(curve, AtomicLine):
        return _distance(curve.start, curve.end)
    if isinstance(curve, AtomicPolyline):
        return float(max(1, len(curve.points) - 1))
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        return curve_length(curve)
    if isinstance(curve, AtomicEllipse):
        return 2.0 * math.pi
    if isinstance(curve, AtomicRectangle):
        return 4.0
    if isinstance(curve, AtomicPolyCurve):
        return sum(polycurve_spans(curve))
    start, end = nurbs_curve_domain(_as_nurbs(curve))
    return end - start


def polycurve_spans(curve: AtomicPolyCurve) -> list[float]:
    """Parameter length of every segment (the stored spans, or the natural ones)."""
    if curve.spans:
        return [float(span) for span in curve.spans]
    return [natural_span(segment) for segment in curve.segments]


def polycurve_breaks(curve: AtomicPolyCurve) -> list[float]:
    """Parameters at which the segments start and end (``segment_count + 1`` values)."""
    breaks = [float(curve.start)]
    for span in polycurve_spans(curve):
        breaks.append(breaks[-1] + span)
    return breaks


def polycurve_locate(curve: AtomicPolyCurve, parameter: float) -> tuple[int, float]:
    """(segment index, local 0..1) for a polycurve parameter; joints belong to the outgoing segment."""
    breaks = polycurve_breaks(curve)
    t = min(breaks[-1], max(breaks[0], float(parameter)))
    index = len(breaks) - 2
    for i in range(len(breaks) - 1):
        if t < breaks[i + 1]:
            index = i
            break
    span = breaks[index + 1] - breaks[index]
    local = 0.0 if span <= _TOLERANCE else (t - breaks[index]) / span
    return index, min(1.0, max(0.0, local))


def segment_parameter(segment, local: float) -> float:
    """Map a local 0..1 position onto a segment's own parameter domain."""
    start, end = curve_domain_of(segment)
    return start + (end - start) * float(local)


def curve_domain_of(curve) -> tuple[float, float]:
    """Parameter domain: [0, 1] for named curve atoms, the knot domain for NURBS, the accumulated
    segment spans for polycurves."""
    if isinstance(curve, _NATIVE_ATOMS):
        return 0.0, 1.0
    if isinstance(curve, AtomicPolyCurve):
        breaks = polycurve_breaks(curve)
        return breaks[0], breaks[-1]
    return nurbs_curve_domain(_as_nurbs(curve))


def _arc_geometry(curve) -> tuple[AtomicPoint, AtomicVector, AtomicVector, float, float, float]:
    """(centre, x axis, y axis, radius, start angle, sweep) of an arc or circle."""
    plane = curve.plane
    if isinstance(curve, AtomicCircle):
        return plane.origin, plane.x_axis, plane.y_axis, float(curve.radius), 0.0, 2.0 * math.pi
    return plane.origin, plane.x_axis, plane.y_axis, float(curve.radius), float(curve.angle.start), float(curve.angle.length)


def _arc_point(curve, angle: float) -> AtomicPoint:
    centre, x_axis, y_axis, radius, _, _ = _arc_geometry(curve)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return AtomicPoint(
        centre.x + radius * (cos_a * x_axis.x + sin_a * y_axis.x),
        centre.y + radius * (cos_a * x_axis.y + sin_a * y_axis.y),
        centre.z + radius * (cos_a * x_axis.z + sin_a * y_axis.z),
    )


def _polyline_segments(curve: AtomicPolyline) -> list[tuple[AtomicPoint, AtomicPoint]]:
    points = list(curve.points)
    return list(zip(points, points[1:]))


def _polyline_locate(curve: AtomicPolyline, parameter: float) -> tuple[int, float]:
    """(segment index, local 0..1) for a uniform-per-segment polyline parameter in [0, 1]."""
    segments = _polyline_segments(curve)
    if not segments:
        raise ValueError("A polyline needs at least two points")
    scaled = min(1.0, max(0.0, float(parameter))) * len(segments)
    index = min(int(math.floor(scaled)), len(segments) - 1)
    return index, scaled - index


def curve_point_at(curve, parameter: float) -> AtomicPoint:
    """Point at *parameter* (see the module note on parameterisations)."""
    if isinstance(curve, AtomicLine):
        return _lerp_point(curve.start, curve.end, float(parameter))
    if isinstance(curve, AtomicPolyline):
        index, local = _polyline_locate(curve, parameter)
        start, end = _polyline_segments(curve)[index]
        return _lerp_point(start, end, local)
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        _, _, _, _, start_angle, sweep = _arc_geometry(curve)
        return _arc_point(curve, start_angle + sweep * float(parameter))
    if isinstance(curve, AtomicPolyCurve):
        index, local = polycurve_locate(curve, parameter)
        segment = curve.segments[index]
        return curve_point_at(segment, segment_parameter(segment, local))
    return evaluate_nurbs_curve(_as_nurbs(curve), float(parameter))


def curve_tangent_at(curve, parameter: float, *, incoming: bool = False) -> AtomicVector:
    """Unit tangent at *parameter*.

    At a polyline vertex the outgoing segment's direction is used (Grasshopper's
    Evaluate Curve); ``incoming=True`` takes the segment ending there instead
    (what Rhino's perpendicular frames do).
    """
    if isinstance(curve, AtomicLine):
        return _unit_between(curve.start, curve.end)
    if isinstance(curve, AtomicPolyline):
        index, local = _polyline_locate(curve, parameter)
        segments = _polyline_segments(curve)
        if not incoming and local >= 1.0 - _TOLERANCE and index + 1 < len(segments):
            index += 1
        elif incoming and local <= _TOLERANCE and index > 0:
            index -= 1
        start, end = segments[index]
        return _unit_between(start, end)
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        _, x_axis, y_axis, _, start_angle, sweep = _arc_geometry(curve)
        angle = start_angle + sweep * float(parameter)
        sign = -1.0 if sweep < 0.0 else 1.0
        return _snap_small(AtomicVector(
            sign * (-math.sin(angle) * x_axis.x + math.cos(angle) * y_axis.x),
            sign * (-math.sin(angle) * x_axis.y + math.cos(angle) * y_axis.y),
            sign * (-math.sin(angle) * x_axis.z + math.cos(angle) * y_axis.z),
        ))
    if isinstance(curve, AtomicPolyCurve):
        index, local = polycurve_locate(curve, parameter)
        if incoming and local <= _TOLERANCE and index > 0:
            index, local = index - 1, 1.0
        segment = curve.segments[index]
        return curve_tangent_at(segment, segment_parameter(segment, local), incoming=incoming)
    return nurbs_curve_tangent(_as_nurbs(curve), float(parameter))


def _snap_small(vector: AtomicVector, tolerance: float = 1e-14) -> AtomicVector:
    """Zero out components that are floating-point noise (cos(pi/2) and friends) on a unit vector."""
    return AtomicVector(*(0.0 if abs(component) < tolerance else component for component in (vector.x, vector.y, vector.z)))


def curve_curvature_vector(curve, parameter: float) -> AtomicVector:
    """Curvature vector (towards the centre of curvature, length = curvature); zero on straights."""
    if isinstance(curve, (AtomicLine, AtomicPolyline)):
        return AtomicVector(0.0, 0.0, 0.0)
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        centre, _, _, radius, start_angle, sweep = _arc_geometry(curve)
        point = _arc_point(curve, start_angle + sweep * float(parameter))
        if radius <= _TOLERANCE:
            return AtomicVector(0.0, 0.0, 0.0)
        return AtomicVector((centre.x - point.x) / (radius * radius), (centre.y - point.y) / (radius * radius), (centre.z - point.z) / (radius * radius))
    if isinstance(curve, AtomicPolyCurve):
        index, local = polycurve_locate(curve, parameter)
        segment = curve.segments[index]
        return curve_curvature_vector(segment, segment_parameter(segment, local))
    from pyhopper.Utils.Nurbs import curve_curvature

    _, _, vector = curve_curvature(_as_nurbs(curve), float(parameter))
    return vector


def curve_derivatives_at(curve, parameter: float) -> tuple[AtomicPoint, AtomicVector, AtomicVector, AtomicVector]:
    """Point and the first three derivatives at *parameter*, in each atom's own parameterisation.

    Lines and polylines (uniform per segment) are exact, arcs and circles are
    differentiated in angle, everything else goes through its NURBS form.
    """
    t = float(parameter)
    zero = AtomicVector(0.0, 0.0, 0.0)
    if isinstance(curve, AtomicLine):
        return curve_point_at(curve, t), AtomicVector(curve.end.x - curve.start.x, curve.end.y - curve.start.y, curve.end.z - curve.start.z), zero, zero
    if isinstance(curve, AtomicPolyline):
        index, local = _polyline_locate(curve, t)
        segments = _polyline_segments(curve)
        start, end = segments[index]
        count = len(segments)
        return _lerp_point(start, end, local), AtomicVector((end.x - start.x) * count, (end.y - start.y) * count, (end.z - start.z) * count), zero, zero
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        centre, x_axis, y_axis, radius, start_angle, sweep = _arc_geometry(curve)
        angle = start_angle + sweep * t
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        radial = AtomicVector(*(radius * (cos_a * x + sin_a * y) for x, y in zip((x_axis.x, x_axis.y, x_axis.z), (y_axis.x, y_axis.y, y_axis.z))))
        first = AtomicVector(*(radius * sweep * (-sin_a * x + cos_a * y) for x, y in zip((x_axis.x, x_axis.y, x_axis.z), (y_axis.x, y_axis.y, y_axis.z))))
        second = AtomicVector(-sweep * sweep * radial.x, -sweep * sweep * radial.y, -sweep * sweep * radial.z)
        third = AtomicVector(-sweep * sweep * first.x, -sweep * sweep * first.y, -sweep * sweep * first.z)
        return AtomicPoint(centre.x + radial.x, centre.y + radial.y, centre.z + radial.z), first, second, third
    if isinstance(curve, AtomicPolyCurve):
        index, local = polycurve_locate(curve, t)
        segment = curve.segments[index]
        seg_start, seg_end = curve_domain_of(segment)
        scale = (seg_end - seg_start) / polycurve_spans(curve)[index]  # d(segment parameter) / d(polycurve parameter)
        point, first, second, third = curve_derivatives_at(segment, seg_start + (seg_end - seg_start) * local)
        return (
            point,
            AtomicVector(first.x * scale, first.y * scale, first.z * scale),
            AtomicVector(second.x * scale * scale, second.y * scale * scale, second.z * scale * scale),
            AtomicVector(third.x * scale ** 3, third.y * scale ** 3, third.z * scale ** 3),
        )
    from pyhopper.Utils.Nurbs import curve_derivatives

    point, (first, second, third) = curve_derivatives(_as_nurbs(curve), t, 3)
    return point, first, second, third


def curve_start_end(curve) -> tuple[AtomicPoint, AtomicPoint]:
    start, end = curve_domain_of(curve)
    return curve_point_at(curve, start), curve_point_at(curve, end)


def curve_is_closed(curve, tolerance: float = 1e-9) -> bool:
    if isinstance(curve, AtomicCircle):
        return True
    if isinstance(curve, AtomicArc):
        return abs(abs(float(curve.angle.length)) - 2.0 * math.pi) <= tolerance
    if isinstance(curve, AtomicLine):
        return False
    if isinstance(curve, AtomicPolyline):
        return curve.is_closed
    if isinstance(curve, AtomicPolyCurve):
        first, last = curve_start_end(curve)
        extent = max(1.0, abs(first.x), abs(first.y), abs(first.z))
        return _distance(first, last) <= tolerance * extent
    return is_closed_nurbs_curve(_as_nurbs(curve), tolerance)


def curve_is_periodic(curve) -> bool:
    """True for circles and for closed NURBS curves whose knot vector is not clamped (Rhino's notion)."""
    if isinstance(curve, AtomicCircle):
        return True
    if isinstance(curve, AtomicNurbsCurve):
        degree = int(curve.degree)
        if len(curve.knots) <= degree or not is_closed_nurbs_curve(curve):
            return False
        return abs(float(curve.knots[0]) - float(curve.knots[degree])) > _TOLERANCE
    return False


def _nurbs_length_table(curve: AtomicNurbsCurve, tolerance: float) -> _LengthTable:
    return _arc_length_table(curve, tolerance)


def curve_length_at(curve, parameter: float, tolerance: float = 1e-7) -> float:
    """Arc length from the curve start to *parameter*."""
    if isinstance(curve, AtomicLine):
        return _distance(curve.start, curve.end) * min(1.0, max(0.0, float(parameter)))
    if isinstance(curve, AtomicPolyline):
        index, local = _polyline_locate(curve, parameter)
        segments = _polyline_segments(curve)
        return sum(_distance(a, b) for a, b in segments[:index]) + _distance(*segments[index]) * local
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        _, _, _, radius, _, sweep = _arc_geometry(curve)
        return radius * abs(sweep) * min(1.0, max(0.0, float(parameter)))
    if isinstance(curve, AtomicPolyCurve):
        index, local = polycurve_locate(curve, parameter)
        segment = curve.segments[index]
        before = sum(curve_length(piece, tolerance) for piece in curve.segments[:index])
        return before + curve_length_at(segment, segment_parameter(segment, local), tolerance)
    nurbs = _as_nurbs(curve)
    return _nurbs_length_table(nurbs, tolerance).length_at(float(parameter))


def curve_parameter_at_length(curve, length: float, tolerance: float = 1e-7) -> float:
    """Parameter at arc length *length* from the start (clamped to the curve)."""
    total = curve_length(curve, tolerance)
    if total <= _TOLERANCE:
        raise ValueError("Cannot measure along a zero-length curve")
    target = min(total, max(0.0, float(length)))
    if isinstance(curve, (AtomicLine, AtomicArc, AtomicCircle)):
        return target / total
    if isinstance(curve, AtomicPolyline):
        segments = _polyline_segments(curve)
        remaining = target
        for index, (a, b) in enumerate(segments):
            span = _distance(a, b)
            if remaining <= span + _TOLERANCE or index == len(segments) - 1:
                local = 0.0 if span <= _TOLERANCE else min(1.0, remaining / span)
                return (index + local) / len(segments)
            remaining -= span
        return 1.0
    if isinstance(curve, AtomicPolyCurve):
        breaks = polycurve_breaks(curve)
        remaining = target
        for index, segment in enumerate(curve.segments):
            piece = curve_length(segment, tolerance)
            if remaining <= piece + _TOLERANCE or index == len(curve.segments) - 1:
                seg_start, seg_end = curve_domain_of(segment)
                local = 0.0 if piece <= _TOLERANCE else (curve_parameter_at_length(segment, min(piece, remaining), tolerance) - seg_start) / (seg_end - seg_start)
                return breaks[index] + (breaks[index + 1] - breaks[index]) * local
            remaining -= piece
        return breaks[-1]
    nurbs = _as_nurbs(curve)
    return _nurbs_length_table(nurbs, tolerance).parameter_at(target)


def curve_kink_angle(curve, parameter: float, tolerance: float = 1e-9) -> float:
    """Angle between the incoming and outgoing tangents at *parameter* (0 where the curve is smooth).

    Polylines kink at their vertices (and at the seam of a closed polyline);
    NURBS curves kink at interior knots of full multiplicity.
    """
    if isinstance(curve, (AtomicLine, AtomicArc, AtomicCircle)):
        return 0.0
    if isinstance(curve, AtomicPolyline):
        segments = _polyline_segments(curve)
        count = len(segments)
        scaled = float(parameter) * count
        vertex = int(round(scaled))
        if abs(scaled - vertex) > tolerance * max(1.0, count):
            return 0.0
        if 0 < vertex < count:
            return _angle_between(_unit_between(*segments[vertex - 1]), _unit_between(*segments[vertex]))
        if curve.is_closed and count >= 2:
            return _angle_between(_unit_between(*segments[-1]), _unit_between(*segments[0]))
        return 0.0
    if isinstance(curve, AtomicPolyCurve):
        breaks = polycurve_breaks(curve)
        t = float(parameter)
        for index, joint in enumerate(breaks):
            if abs(t - joint) <= tolerance * max(1.0, abs(breaks[-1] - breaks[0])):
                if 0 < index < len(breaks) - 1:
                    return _angle_between(curve_tangent_at(curve, joint, incoming=True), curve_tangent_at(curve, joint))
                if curve_is_closed(curve):
                    return _angle_between(curve_tangent_at(curve, breaks[-1], incoming=True), curve_tangent_at(curve, breaks[0]))
                return 0.0
        index, local = polycurve_locate(curve, t)
        segment = curve.segments[index]
        return curve_kink_angle(segment, segment_parameter(segment, local), tolerance)
    nurbs = _as_nurbs(curve)
    start, end = nurbs_curve_domain(nurbs)
    degree = int(nurbs.degree)
    interior = [knot for knot in nurbs.knots if start < knot < end]
    for knot in sorted(set(interior)):
        if interior.count(knot) >= degree and abs(float(parameter) - knot) <= tolerance * max(1.0, abs(end - start)):
            step = (end - start) * 1e-6
            incoming = nurbs_curve_tangent(nurbs, max(start, knot - step))
            outgoing = nurbs_curve_tangent(nurbs, min(end, knot + step))
            return _angle_between(incoming, outgoing)
    return 0.0


def divide_curve_by_count(curve, count: int, tolerance: float = 1e-7) -> tuple[list[AtomicPoint], list[AtomicVector], list[float]]:
    """Equal arc-length division of any curve atom (Grasshopper Divide Curve).

    Open curves yield ``count + 1`` points, closed curves ``count`` (the seam is
    not repeated). Parameters follow each atom's own parameterisation.
    """
    segments = int(count)
    if segments < 1:
        raise ValueError("Divide Curve requires at least one segment")
    total = curve_length(curve, tolerance)
    if total <= _TOLERANCE:
        raise ValueError("Divide Curve requires a non-zero-length curve")
    start, end = curve_domain_of(curve)
    point_count = segments if curve_is_closed(curve) else segments + 1
    parameters = []
    for index in range(point_count):
        if index == 0:
            parameters.append(start)
        elif index == segments:
            parameters.append(end)
        else:
            parameters.append(curve_parameter_at_length(curve, total * index / segments, tolerance))
    return sample_curve(curve, parameters)


def divide_curve_by_length(curve, length: float, tolerance: float = 1e-7) -> tuple[list[AtomicPoint], list[AtomicVector], list[float]]:
    """Points every *length* along the curve from its start (Grasshopper Divide Length).

    The start is always included, the end only when the length divides the curve
    exactly; on a closed curve the final point (which is the start again) is
    left out.
    """
    step = float(length)
    if step <= _TOLERANCE:
        raise ValueError("Divide Length requires a length greater than zero")
    total = curve_length(curve, tolerance)
    if total <= _TOLERANCE:
        raise ValueError("Divide Length requires a non-zero-length curve")
    count = int(math.floor((total + tolerance * max(1.0, total)) / step))
    targets = [index * step for index in range(count + 1)]
    if curve_is_closed(curve) and len(targets) > 1 and abs(targets[-1] - total) <= tolerance * max(1.0, total):
        targets.pop()
    parameters = [curve_parameter_at_length(curve, target, tolerance) for target in targets]
    return sample_curve(curve, parameters)


def sample_curve(curve, parameters: list[float]) -> tuple[list[AtomicPoint], list[AtomicVector], list[float]]:
    """Points and unit tangents at *parameters* (returned together with the parameters)."""
    points = [curve_point_at(curve, parameter) for parameter in parameters]
    tangents = [curve_tangent_at(curve, parameter) for parameter in parameters]
    return points, tangents, parameters


def redomain_nurbs_curve(curve: AtomicNurbsCurve, domain: tuple[float, float]) -> AtomicNurbsCurve:
    """Map the knot vector affinely onto *domain*; the geometry is untouched."""
    start, end = nurbs_curve_domain(curve)
    span = end - start
    new_start, new_end = float(domain[0]), float(domain[1])
    if abs(span) <= _TOLERANCE or abs(new_end - new_start) <= _TOLERANCE:
        raise ValueError("Cannot re-domain a curve onto a zero-length domain")
    knots = tuple(new_start + (float(knot) - start) / span * (new_end - new_start) for knot in curve.knots)
    return AtomicNurbsCurve(control_points=curve.control_points, weights=curve.weights, knots=knots, degree=curve.degree)


def _lerp_point(a: AtomicPoint, b: AtomicPoint, t: float) -> AtomicPoint:
    return AtomicPoint(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t)


def _unit_between(a: AtomicPoint, b: AtomicPoint) -> AtomicVector:
    vector = AtomicVector(b.x - a.x, b.y - a.y, b.z - a.z)
    length = math.sqrt(vector.x * vector.x + vector.y * vector.y + vector.z * vector.z)
    if length <= _TOLERANCE:
        return AtomicVector(0.0, 0.0, 0.0)
    return AtomicVector(vector.x / length, vector.y / length, vector.z / length)


def _angle_between(a: AtomicVector, b: AtomicVector) -> float:
    dot = a.x * b.x + a.y * b.y + a.z * b.z
    return math.acos(max(-1.0, min(1.0, dot)))


def curve_segments(curve) -> list[tuple[float, float, float]]:
    """``(start parameter, end parameter, length)`` per segment: one per polyline edge, else the whole curve."""
    if isinstance(curve, AtomicPolyline):
        segments = _polyline_segments(curve)
        count = len(segments)
        return [(index / count, (index + 1) / count, _distance(start, end)) for index, (start, end) in enumerate(segments)]
    if isinstance(curve, AtomicPolyCurve):
        breaks = polycurve_breaks(curve)
        return [(breaks[index], breaks[index + 1], curve_length(segment)) for index, segment in enumerate(curve.segments)]
    start, end = curve_domain_of(curve)
    return [(start, end, curve_length(curve))]


def curve_planarity(curve, samples: int = 256) -> tuple[AtomicPlane, float]:
    """``(plane, deviation)`` for any curve atom.

    Arcs, circles and rectangles report their own plane; a line lies in the
    plane through it whose normal is world Z rejected from the direction (then
    X); a planar polyline reports its first vertex, Newell normal and first
    segment; everything else is the least-squares plane of ``samples`` points
    along the curve with the largest distance as deviation.
    """
    from pyhopper.Utils.Fitting import fit_plane  # local import: Fitting depends on Vectors only

    if isinstance(curve, (AtomicArc, AtomicCircle, AtomicRectangle)):
        return curve.plane, 0.0
    if isinstance(curve, AtomicLine):
        direction = _unit_between(curve.start, curve.end)
        for reference in (AtomicVector(0.0, 0.0, 1.0), AtomicVector(1.0, 0.0, 0.0)):
            normal = _reject_vector(reference, direction)
            if normal.length > 1e-9:
                return AtomicPlane(curve.start, normal, direction), 0.0
        return AtomicPlane(curve.start, AtomicVector(0.0, 0.0, 1.0), AtomicVector(1.0, 0.0, 0.0)), 0.0
    if isinstance(curve, AtomicPolyline):
        points = list(curve.points)
        if len(points) >= 3:
            from pyhopper.Utils.Planes import newell_normal

            normal = newell_normal(points)
            if normal.length > 1e-9:
                deviation = max(abs(_dot((p.x - points[0].x, p.y - points[0].y, p.z - points[0].z), normal.unitize())) for p in points)
                if deviation <= 1e-9:
                    return AtomicPlane(points[0], normal, _unit_between(points[0], points[1])), 0.0
    start, end = curve_domain_of(curve)
    sampled = [curve_point_at(curve, start + (end - start) * index / samples) for index in range(samples + 1)]
    return fit_plane(sampled)


def _reject_vector(vector: AtomicVector, direction: AtomicVector) -> AtomicVector:
    projection = vector.x * direction.x + vector.y * direction.y + vector.z * direction.z
    return AtomicVector(vector.x - projection * direction.x, vector.y - projection * direction.y, vector.z - projection * direction.z)


def _dot(a, b: AtomicVector) -> float:
    return a[0] * b.x + a[1] * b.y + a[2] * b.z
