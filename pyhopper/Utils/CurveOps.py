"""CurveOps - splitting, joining, exploding, extending, re-seaming, filleting,
dashing and blending curves (the K2 + K5 wave of the component roadmap),
with the conventions read off Grasshopper 8.

Parameter spans of polycurve segments follow two rules (both Rhino's):
*pieces* of an input curve keep their parameter length in the input's own
domain; *new* segments (fillet arcs, blends, joined whole curves, extension
lines) get their natural span (``Curves.natural_span``).
"""

from __future__ import annotations

import math
from typing import Sequence

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicEllipse,
    AtomicInterval,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyCurve,
    AtomicPolyline,
    AtomicRectangle,
    AtomicVector,
)
from pyhopper.Utils.CurveFitting import reverse_curve
from pyhopper.Utils.Curves import (
    curve_derivatives_at,
    curve_domain_of,
    curve_is_closed,
    curve_length,
    curve_parameter_at_length,
    curve_point_at,
    curve_tangent_at,
    natural_span,
    nurbs_curve_length,
    polycurve_breaks,
    polycurve_locate,
    polycurve_spans,
    segment_parameter,
)
from pyhopper.Utils.NurbsEditing import extend_nurbs_domain, join_nurbs_curves, redomain, sub_nurbs_curve
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Utils.Vectors import cross, distance, dot, is_zero, length, scale, sub, unit

_TOLERANCE = 1e-9
JOIN_TOLERANCE = 1e-6


# ── basics ─────────────────────────────────────────────────────────


def _pt(p) -> AtomicPoint:
    return AtomicPoint(float(p.x), float(p.y), float(p.z))


def _move(p, v, factor: float = 1.0) -> AtomicPoint:
    return AtomicPoint(p.x + v.x * factor, p.y + v.y * factor, p.z + v.z * factor)


def curve_endpoints(curve) -> tuple[AtomicPoint, AtomicPoint]:
    start, end = curve_domain_of(curve)
    return curve_point_at(curve, start), curve_point_at(curve, end)


def polycurve(segments: Sequence, spans: Sequence[float] | None = None, start: float = 0.0) -> AtomicPolyCurve:
    """Build a polycurve; ``spans`` default to the natural spans."""
    segments = tuple(segments)
    return AtomicPolyCurve(segments, tuple(float(s) for s in (spans if spans is not None else [natural_span(s) for s in segments])), float(start))


def _as_polyline(curve) -> AtomicPolyline | None:
    """Polylines, rectangles and polycurves made of straight pieces as one polyline (else ``None``)."""
    if isinstance(curve, AtomicPolyline):
        return curve
    if isinstance(curve, AtomicRectangle):
        return AtomicPolyline(tuple(_polyline_points(as_nurbs_curve(curve))))
    if isinstance(curve, AtomicLine):
        return AtomicPolyline((curve.start, curve.end))
    if isinstance(curve, AtomicPolyCurve):
        points: list[AtomicPoint] = []
        for segment in curve.segments:
            piece = _as_polyline(segment)
            if piece is None:
                return None
            for point in piece.points:
                if not points or distance(points[-1], point) > _TOLERANCE:
                    points.append(point)
        return AtomicPolyline(tuple(points))
    return None


def _polyline_points(nurbs: AtomicNurbsCurve) -> list[AtomicPoint]:
    return list(nurbs.control_points)


# ── pieces ─────────────────────────────────────────────────────────


def sub_curve(curve, start: float, end: float):
    """The piece of *curve* between two parameters (order-free, clamped to the domain), typed like
    the input: lines stay lines, arcs and circles give arcs, polylines give polylines, NURBS keep their
    knot sub-domain and polycurves give sub-polycurves."""
    domain_start, domain_end = curve_domain_of(curve)
    a, b = max(domain_start, min(float(start), float(end))), min(domain_end, max(float(start), float(end)))
    if b - a <= _TOLERANCE * max(1.0, domain_end - domain_start):
        raise ValueError("The curve piece is empty")
    if isinstance(curve, AtomicLine):
        return AtomicLine(curve_point_at(curve, a), curve_point_at(curve, b))
    if isinstance(curve, AtomicPolyline):
        count = len(curve.points) - 1
        points = [curve_point_at(curve, a)]
        for index in range(1, count):
            vertex_parameter = index / count
            if a + _TOLERANCE < vertex_parameter < b - _TOLERANCE:
                points.append(curve.points[index])
        points.append(curve_point_at(curve, b))
        return AtomicPolyline(tuple(points))
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        if isinstance(curve, AtomicCircle):
            angle_start, sweep = 0.0, 2.0 * math.pi
        else:
            angle_start, sweep = float(curve.angle.start), float(curve.angle.length)
        return AtomicArc(curve.plane, curve.radius, AtomicInterval(angle_start + sweep * a, angle_start + sweep * b))
    if isinstance(curve, AtomicPolyCurve):
        return _sub_polycurve(curve, a, b)
    if isinstance(curve, AtomicRectangle):
        return sub_curve(_as_polyline(curve), a, b)
    nurbs = as_nurbs_curve(curve)
    if a <= domain_start + _TOLERANCE and b >= domain_end - _TOLERANCE:
        return curve
    return sub_nurbs_curve(nurbs, a, b)


def _sub_polycurve(curve: AtomicPolyCurve, a: float, b: float):
    breaks = polycurve_breaks(curve)
    spans = polycurve_spans(curve)
    first, first_local = polycurve_locate(curve, a)
    last, last_local = polycurve_locate(curve, b)
    if last_local <= _TOLERANCE and last > first:
        last, last_local = last - 1, 1.0
    segments, new_spans = [], []
    for index in range(first, last + 1):
        segment = curve.segments[index]
        lo = first_local if index == first else 0.0
        hi = last_local if index == last else 1.0
        if hi - lo <= _TOLERANCE:
            continue
        seg_start, seg_end = curve_domain_of(segment)
        piece = segment if lo <= _TOLERANCE and hi >= 1.0 - _TOLERANCE else sub_curve(segment, seg_start + (seg_end - seg_start) * lo, seg_start + (seg_end - seg_start) * hi)
        segments.append(piece)
        new_spans.append(spans[index] * (hi - lo))
    return AtomicPolyCurve(tuple(segments), tuple(new_spans), a)


def shatter(curve, parameters: Sequence[float]) -> list:
    """Grasshopper's Shatter: split at the (sorted, de-duplicated, in-domain) parameters; closed curves
    give the wrap-around piece last as a two-piece polycurve. No parameters at all gives no pieces;
    parameters only at the ends give the whole curve."""
    start, end = curve_domain_of(curve)
    extent = max(1.0, end - start)
    cuts: list[float] = []
    for value in sorted(float(t) for t in parameters):
        if start + _TOLERANCE * extent < value < end - _TOLERANCE * extent and (not cuts or value - cuts[-1] > _TOLERANCE * extent):
            cuts.append(value)
    if not cuts:
        return [curve] if len(parameters) else []
    if curve_is_closed(curve):
        pieces = [sub_curve(curve, cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]
        tail, head = sub_curve(curve, cuts[-1], end), sub_curve(curve, start, cuts[0])
        pieces.append(AtomicPolyCurve((tail, head), (end - cuts[-1], cuts[0] - start), cuts[-1]))
        return pieces
    bounds = [start] + cuts + [end]
    return [sub_curve(curve, bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]


# ── explode ────────────────────────────────────────────────────────


def _kink_knots(nurbs: AtomicNurbsCurve) -> list[float]:
    start, end = curve_domain_of(nurbs)
    degree = int(nurbs.degree)
    knots = [float(k) for k in nurbs.knots]
    seen: list[float] = []
    for knot in knots:
        if start < knot < end and knots.count(knot) >= degree and knot not in seen:
            seen.append(knot)
    return seen


def explode(curve, recursive: bool = True) -> tuple[list, list[AtomicPoint]]:
    """Grasshopper's Explode: the curve's segments (polyline edges as lines, polycurve segments —
    nested ones exploded too when *recursive* — NURBS curves split at their kinks) and the vertices
    between them, ends included (a closed curve repeats its start)."""
    if isinstance(curve, AtomicLine):
        return [curve], [curve.start, curve.end]
    if isinstance(curve, (AtomicPolyline, AtomicRectangle)):
        polyline = _as_polyline(curve)
        points = list(polyline.points)
        return [AtomicLine(a, b) for a, b in zip(points, points[1:])], points
    if isinstance(curve, (AtomicArc, AtomicCircle, AtomicEllipse)):
        first, last = curve_endpoints(curve)
        return [curve], [first, last]
    if isinstance(curve, AtomicPolyCurve):
        segments: list = []
        for segment in curve.segments:
            if recursive and isinstance(segment, (AtomicPolyCurve, AtomicPolyline, AtomicRectangle)):
                segments.extend(explode(segment, True)[0])
            else:
                segments.append(segment)
        vertices = [curve_endpoints(segments[0])[0]] + [curve_endpoints(segment)[1] for segment in segments]
        return segments, vertices
    nurbs = as_nurbs_curve(curve)
    kinks = _kink_knots(nurbs)
    if not kinks:
        first, last = curve_endpoints(curve)
        return [curve], [first, last]
    start, end = curve_domain_of(nurbs)
    bounds = [start] + kinks + [end]
    return [sub_nurbs_curve(nurbs, bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)], [curve_point_at(nurbs, t) for t in bounds]


# ── extend ─────────────────────────────────────────────────────────


def _end_speed(curve, parameter: float) -> float:
    _, first, _, _ = curve_derivatives_at(curve, parameter)
    speed = length(first)
    if speed <= _TOLERANCE:
        raise ValueError("Cannot extend a curve with a stationary end")
    return speed


def _extension_arc(point: AtomicPoint, tangent: AtomicVector, curvature: AtomicVector, extension: float, at_start: bool):
    """Arc (or line when straight) continuing the curve beyond one end with its end curvature."""
    kappa = length(curvature)
    if kappa <= 1e-9:
        return AtomicLine(_move(point, tangent, -extension), point) if at_start else AtomicLine(point, _move(point, tangent, extension))
    radius = 1.0 / kappa
    centre = _move(point, unit(curvature), radius)
    x_axis = unit(sub(point, centre))
    normal = unit(cross(x_axis, tangent))
    sweep = extension / radius
    angles = AtomicInterval(-sweep, 0.0) if at_start else AtomicInterval(0.0, sweep)
    return AtomicArc(AtomicPlane(centre, normal, x_axis), radius, angles)


def _trim_by_length(curve, cut_start: float, cut_end: float):
    total = curve_length(curve)
    if cut_start + cut_end >= total - _TOLERANCE:
        raise ValueError("Cannot trim a curve to nothing")
    start, end = curve_domain_of(curve)
    a = curve_parameter_at_length(curve, cut_start) if cut_start > 0 else start
    b = curve_parameter_at_length(curve, total - cut_end) if cut_end > 0 else end
    return sub_curve(curve, a, b)


def extend_curve(curve, kind: int, start_length: float, end_length: float):
    """Grasshopper's Extend Curve: *kind* 1 continues with the end curvature (arcs), 2 extends the
    curve itself smoothly (lines and polylines grow, arcs sweep further, NURBS curves extrapolate
    their end spans), anything else appends straight lines. Negative lengths trim by arc length; closed
    curves are returned unchanged. Extension pieces get the parameter span Rhino gives them
    (``length / speed`` at that end)."""
    l0, l1 = float(start_length), float(end_length)
    if curve_is_closed(curve) or (abs(l0) <= _TOLERANCE and abs(l1) <= _TOLERANCE):
        return curve
    if l0 < 0.0 or l1 < 0.0:
        curve = _trim_by_length(curve, max(0.0, -l0), max(0.0, -l1))
        l0, l1 = max(0.0, l0), max(0.0, l1)
        if l0 <= _TOLERANCE and l1 <= _TOLERANCE:
            return curve
    if int(kind) == 2:
        return _extend_smooth(curve, l0, l1)
    start, end = curve_domain_of(curve)
    segments, spans = [curve], [end - start]
    first_point, last_point = curve_endpoints(curve)
    if l0 > _TOLERANCE:
        point, first, _, _ = curve_derivatives_at(curve, start)
        tangent = unit(first)
        piece = _extension_arc(first_point, tangent, _curvature_vector(curve, start), l0, True) if int(kind) == 1 else AtomicLine(_move(first_point, tangent, -l0), first_point)
        segments.insert(0, piece)
        spans.insert(0, l0 / _end_speed(curve, start))
    if l1 > _TOLERANCE:
        point, first, _, _ = curve_derivatives_at(curve, end)
        tangent = unit(first)
        piece = _extension_arc(last_point, tangent, _curvature_vector(curve, end), l1, False) if int(kind) == 1 else AtomicLine(last_point, _move(last_point, tangent, l1))
        segments.append(piece)
        spans.append(l1 / _end_speed(curve, end))
    return AtomicPolyCurve(tuple(segments), tuple(spans), start - (spans[0] if l0 > _TOLERANCE else 0.0))


def _curvature_vector(curve, parameter: float) -> AtomicVector:
    from pyhopper.Utils.Curves import curve_curvature_vector

    return curve_curvature_vector(curve, parameter)


def _extend_smooth(curve, l0: float, l1: float):
    if isinstance(curve, AtomicLine):
        direction = unit(sub(curve.end, curve.start))
        return AtomicLine(_move(curve.start, direction, -l0), _move(curve.end, direction, l1))
    if isinstance(curve, AtomicPolyline):
        points = list(curve.points)
        if l0 > _TOLERANCE:
            points[0] = _move(points[0], unit(sub(points[1], points[0])), -l0)
        if l1 > _TOLERANCE:
            points[-1] = _move(points[-1], unit(sub(points[-1], points[-2])), l1)
        return AtomicPolyline(tuple(points))
    if isinstance(curve, AtomicArc):
        radius = abs(float(curve.radius))
        sweep_sign = 1.0 if float(curve.angle.length) >= 0 else -1.0
        return AtomicArc(curve.plane, curve.radius, AtomicInterval(float(curve.angle.start) - sweep_sign * l0 / radius, float(curve.angle.end) + sweep_sign * l1 / radius))
    if isinstance(curve, AtomicPolyCurve):
        segments, spans = list(curve.segments), polycurve_spans(curve)
        start = float(curve.start)
        if l0 > _TOLERANCE:
            old = natural_span(segments[0]) if not isinstance(segments[0], AtomicNurbsCurve) else curve_domain_of(segments[0])[1] - curve_domain_of(segments[0])[0]
            segments[0] = _extend_smooth(segments[0], l0, 0.0)
            new = natural_span(segments[0]) if not isinstance(segments[0], AtomicNurbsCurve) else curve_domain_of(segments[0])[1] - curve_domain_of(segments[0])[0]
            grown = spans[0] * new / old
            start -= grown - spans[0]
            spans[0] = grown
        if l1 > _TOLERANCE:
            old = natural_span(segments[-1]) if not isinstance(segments[-1], AtomicNurbsCurve) else curve_domain_of(segments[-1])[1] - curve_domain_of(segments[-1])[0]
            segments[-1] = _extend_smooth(segments[-1], 0.0, l1)
            new = natural_span(segments[-1]) if not isinstance(segments[-1], AtomicNurbsCurve) else curve_domain_of(segments[-1])[1] - curve_domain_of(segments[-1])[0]
            spans[-1] = spans[-1] * new / old
        return AtomicPolyCurve(tuple(segments), tuple(spans), start)
    nurbs = as_nurbs_curve(curve)
    start, end = curve_domain_of(nurbs)
    new_start = start - _extension_parameter(nurbs, l0, True) if l0 > _TOLERANCE else start
    new_end = end + _extension_parameter(nurbs, l1, False) if l1 > _TOLERANCE else end
    return extend_nurbs_domain(nurbs, new_start, new_end)


def _extension_parameter(nurbs: AtomicNurbsCurve, extension: float, at_start: bool) -> float:
    """Parameter length whose polynomial extrapolation has arc length *extension* (bisection)."""
    start, end = curve_domain_of(nurbs)
    speed = _end_speed(nurbs, start if at_start else end)

    def piece_length(delta: float) -> float:
        extended = extend_nurbs_domain(nurbs, start - delta, end) if at_start else extend_nurbs_domain(nurbs, start, end + delta)
        piece = sub_nurbs_curve(extended, start - delta, start) if at_start else sub_nurbs_curve(extended, end, end + delta)
        return nurbs_curve_length(piece, 1e-10)

    low, high = 0.0, extension / speed
    while piece_length(high) < extension:
        high *= 2.0
    for _ in range(60):
        mid = 0.5 * (low + high)
        if piece_length(mid) < extension:
            low = mid
        else:
            high = mid
        if high - low <= 1e-13 * max(1.0, high):
            break
    return 0.5 * (low + high)


# ── seam ───────────────────────────────────────────────────────────


def change_seam(curve, parameter: float):
    """Grasshopper's Seam: move the start of a closed curve to *parameter* (open curves are returned
    unchanged, as Grasshopper does with a warning). Circles rotate their plane, closed polylines
    rotate their vertices (adding one mid-edge), closed NURBS curves are split and rejoined with a
    C0 knot at the old seam, polycurves rotate their segments."""
    if not curve_is_closed(curve):
        return curve
    start, end = curve_domain_of(curve)
    span = end - start
    t = start + ((float(parameter) - start) % span) if span > 0 else start
    if isinstance(curve, (AtomicCircle, AtomicArc)):
        if isinstance(curve, AtomicCircle):
            angle = 2.0 * math.pi * (t - start) / span
        else:
            angle = float(curve.angle.start) + float(curve.angle.length) * (t - start) / span
        plane = curve.plane
        y_axis = cross(plane.normal, plane.x_axis)
        x_axis = AtomicVector(
            math.cos(angle) * plane.x_axis.x + math.sin(angle) * y_axis.x,
            math.cos(angle) * plane.x_axis.y + math.sin(angle) * y_axis.y,
            math.cos(angle) * plane.x_axis.z + math.sin(angle) * y_axis.z,
        )
        return AtomicCircle(AtomicPlane(plane.origin, plane.normal, x_axis), curve.radius)
    if isinstance(curve, (AtomicPolyline, AtomicRectangle)):
        polyline = _as_polyline(curve)
        points = list(polyline.points[:-1])
        count = len(points)
        scaled = (t - start) / span * count
        index = min(int(math.floor(scaled + 1e-9)), count - 1)
        local = scaled - index
        if local <= 1e-9 or local >= 1.0 - 1e-9:
            vertex = (index + (1 if local >= 1.0 - 1e-9 else 0)) % count
            rotated = points[vertex:] + points[:vertex]
            return AtomicPolyline(tuple(rotated + [rotated[0]]))
        new_vertex = curve_point_at(polyline, t)
        rotated = [new_vertex] + points[index + 1 :] + points[: index + 1] + [new_vertex]
        return AtomicPolyline(tuple(rotated))
    if abs(t - start) <= _TOLERANCE * max(1.0, span):
        return curve
    if isinstance(curve, AtomicPolyCurve):
        after, before = _sub_polycurve(curve, t, end), _sub_polycurve(curve, start, t)
        return AtomicPolyCurve(after.segments + before.segments, after.spans + before.spans, start)
    nurbs = as_nurbs_curve(curve)
    after, before = sub_nurbs_curve(nurbs, t, end), sub_nurbs_curve(nurbs, start, t)
    return join_nurbs_curves([after, before], [start, start + (end - t), end])


# ── join ───────────────────────────────────────────────────────────


def _is_straight(curve) -> bool:
    return isinstance(curve, (AtomicLine, AtomicPolyline))


def join_curves(curves: Sequence, preserve_direction: bool = False, tolerance: float = JOIN_TOLERANCE) -> list:
    """Grasshopper's Join Curves: chain curves whose ends coincide (within *tolerance*). Each chain is
    seeded by the first unused curve; candidates are prepended when their end meets the chain start,
    appended when their start meets the chain end and — unless *preserve_direction* — flipped to fit
    when they meet start-to-start or end-to-end (chains of straight pieces are flipped instead of the
    candidate, as Rhino does when it merges polylines). Chains of lines and polylines become one
    polyline, mixed chains a polycurve with natural spans whose domain starts where the first
    segment's does (a flipped first segment starts at minus its span, Rhino's negated domain), lone
    curves stay as they are."""
    remaining = list(curves)
    results = []
    while remaining:
        chain: list[tuple] = [(remaining.pop(0), False)]  # (curve, flipped by the join)
        changed = True
        while changed and remaining:
            changed = False
            chain_start, chain_end = curve_endpoints(chain[0][0])[0], curve_endpoints(chain[-1][0])[1]
            for index, candidate in enumerate(remaining):
                c_start, c_end = curve_endpoints(candidate)
                if distance(c_end, chain_start) <= tolerance:
                    chain.insert(0, (candidate, False))
                elif distance(c_start, chain_end) <= tolerance:
                    chain.append((candidate, False))
                elif not preserve_direction and distance(c_start, chain_start) <= tolerance:
                    if all(_is_straight(c) for c, _ in chain) and _is_straight(candidate):
                        chain = [(reverse_curve(c), not flipped) for c, flipped in reversed(chain)] + [(candidate, False)]
                    else:
                        chain.insert(0, (reverse_curve(candidate), True))
                elif not preserve_direction and distance(c_end, chain_end) <= tolerance:
                    if all(_is_straight(c) for c, _ in chain) and _is_straight(candidate):
                        chain = [(candidate, False)] + [(reverse_curve(c), not flipped) for c, flipped in reversed(chain)]
                    else:
                        chain.append((reverse_curve(candidate), True))
                else:
                    continue
                remaining.pop(index)
                changed = True
                break
        results.append(_assemble_chain(chain, preserve_direction))
    return results


def _assemble_chain(chain: list[tuple], preserve_direction: bool):
    curves = [c for c, _ in chain]
    if len(curves) == 1:
        # Rhino hands a lone line back as a two-point polyline (unless directions are preserved)
        if isinstance(curves[0], AtomicLine) and not preserve_direction:
            return AtomicPolyline((curves[0].start, curves[0].end))
        return curves[0]
    if all(_is_straight(c) for c in curves):
        points: list[AtomicPoint] = []
        for piece in curves:
            for point in _as_polyline(piece).points:
                if not points or distance(points[-1], point) > _TOLERANCE:
                    points.append(point)
        if len(points) > 2 and distance(points[0], points[-1]) <= JOIN_TOLERANCE:
            points[-1] = points[0]
        return AtomicPolyline(tuple(points))
    first, flipped = chain[0]
    start = -natural_span(first) if flipped else curve_domain_of(first)[0]
    return polycurve(curves, None, start)


# ── fillets ────────────────────────────────────────────────────────


def _corner_arc(vertex: AtomicPoint, incoming: AtomicVector, outgoing: AtomicVector, tangent_length: float) -> AtomicArc:
    """Arc tangent to both edges at ``tangent_length`` from the corner (plane: centre, x towards the
    first tangent point, normal so the arc runs in the incoming direction)."""
    theta = math.acos(max(-1.0, min(1.0, dot(incoming, outgoing))))
    radius = tangent_length / math.tan(theta / 2.0)
    t0, t1 = _move(vertex, incoming, -tangent_length), _move(vertex, outgoing, tangent_length)
    bisector = unit(sub(outgoing, incoming))
    centre = _move(vertex, bisector, radius / math.cos(theta / 2.0))
    x_axis = unit(sub(t0, centre))
    normal = unit(cross(x_axis, incoming))
    return AtomicArc(AtomicPlane(centre, normal, x_axis), radius, AtomicInterval(0.0, theta))


def _corner_parameters(polyline: AtomicPolyline) -> list[int]:
    count = len(polyline.points) - 1
    corners = list(range(1, count))
    if polyline.is_closed:
        corners.insert(0, 0)
    return corners


def _edge_directions(polyline: AtomicPolyline, vertex: int) -> tuple[AtomicVector, AtomicVector, float, float] | None:
    points = polyline.points
    count = len(points) - 1
    previous = points[vertex - 1] if vertex > 0 else points[count - 1]
    following = points[vertex + 1]
    d_in, d_out = sub(points[vertex], previous), sub(following, points[vertex])
    if is_zero(d_in, 1e-12) or is_zero(d_out, 1e-12):
        return None
    if length(cross(unit(d_in), unit(d_out))) <= 1e-12 and dot(d_in, d_out) > 0:
        return None  # collinear: nothing to fillet
    return unit(d_in), unit(d_out), length(d_in), length(d_out)


def fillet_at(curve, parameter: float, radius: float):
    """Grasshopper's Fillet: round the corner nearest to *parameter* with an arc of *radius*. Returns
    ``(curve, corner parameter)``; when there is no corner, the radius does not fit or the radius is
    zero the curve comes back unchanged (with the input parameter, or ``None`` for a zero radius)."""
    r = float(radius)
    polyline = _as_polyline(curve)
    if r <= _TOLERANCE:
        return curve, None
    if polyline is None or len(polyline.points) < 3:
        return curve, float(parameter)
    corners = _corner_parameters(polyline)
    if not corners:
        return curve, float(parameter)
    count = len(polyline.points) - 1
    start, end = curve_domain_of(curve)
    span = end - start
    t = float(parameter)

    def parameter_of(vertex: int) -> float:
        return start + span * vertex / count

    def separation(vertex: int) -> float:
        gap = abs(t - parameter_of(vertex))
        return min(gap, span - gap) if polyline.is_closed else gap

    vertex = min(corners, key=separation)
    edges = _edge_directions(polyline, vertex)
    if edges is None:
        return curve, float(parameter)
    d_in, d_out, len_in, len_out = edges
    theta = math.acos(max(-1.0, min(1.0, dot(d_in, d_out))))
    tangent_length = r * math.tan(theta / 2.0)
    if tangent_length > min(len_in, len_out) + _TOLERANCE:
        return curve, float(parameter)
    arc = _corner_arc(polyline.points[vertex], d_in, d_out, tangent_length)
    t_before = parameter_of(vertex) - span * tangent_length / (len_in * count)
    t_after = parameter_of(vertex) + span * tangent_length / (len_out * count)
    if polyline.is_closed and vertex == 0:
        # the seam corner: one piece runs from the corner's exit tangent point all the way round
        wrapped = t_before + span
        piece = sub_curve(polyline, t_after, wrapped)
        return AtomicPolyCurve((piece, arc), (wrapped - t_after, natural_span(arc)), t_after), parameter_of(vertex)
    if polyline.is_closed:
        # another corner of a closed polyline: Rhino puts the arc first and the piece (running through
        # the seam) after it, with the domain starting where that piece ends
        tail, head = sub_curve(polyline, t_after, end), sub_curve(polyline, start, t_before)
        piece = AtomicPolyline(tuple(tail.points) + tuple(head.points[1:]))
        return AtomicPolyCurve((arc, piece), (natural_span(arc), (end - t_after) + (t_before - start)), t_before + span), parameter_of(vertex)
    before, after = sub_curve(polyline, start, t_before), sub_curve(polyline, t_after, end)
    return AtomicPolyCurve((before, arc, after), (t_before - start, natural_span(arc), end - t_after), start), parameter_of(vertex)


def fillet_distance(curve, distance_value: float):
    """Grasshopper's Fillet Distance: round every corner of a polyline with arcs whose tangent points
    sit *distance* from the corner (clamped to half of an interior edge). Zero distance returns the
    curve, a negative one raises; when the distance does not fit an end edge (or there is no corner)
    the curve comes back wrapped in a polycurve, as Grasshopper does."""
    d = float(distance_value)
    if d < 0.0:
        raise ValueError("Distance must be larger than or equal to zero")
    if d <= _TOLERANCE:
        return curve
    return _fillet_all_corners(curve, lambda theta: d, True)


def fillet_radius(curve, radius: float):
    """Grasshopper's Fillet (radius): round every corner of a polyline with arcs of *radius*; a tangent
    length ``r·tan(θ/2)`` that does not fit is clamped to what the edges allow (half of a shared edge),
    shrinking that arc, as Grasshopper does. Zero returns the curve unchanged, a negative radius
    raises, a curve without corners comes back wrapped in a polycurve."""
    r = float(radius)
    if r < 0.0:
        raise ValueError("Radius must be larger than or equal to zero")
    if r <= _TOLERANCE:
        return curve
    return _fillet_all_corners(curve, lambda theta: r * math.tan(theta / 2.0), False)


def _fillet_all_corners(curve, tangent_for_angle, give_up_on_end_edges: bool):
    polyline = _as_polyline(curve)
    if polyline is None or len(polyline.points) < 3:
        return polycurve((curve,))
    corners = _corner_parameters(polyline)
    points = polyline.points
    count = len(points) - 1
    edge_lengths = [distance(points[i], points[i + 1]) for i in range(count)]
    closed = polyline.is_closed
    arcs: dict[int, AtomicArc | None] = {}
    for vertex in corners:
        edges = _edge_directions(polyline, vertex)
        if edges is None:
            arcs[vertex] = None
            continue
        d_in, d_out = edges[0], edges[1]
        theta = math.acos(max(-1.0, min(1.0, dot(d_in, d_out))))
        wanted = tangent_for_angle(theta)
        allowed = wanted
        for edge in ((vertex - 1) % count, vertex % count):
            shared = closed or edge not in (0, count - 1)
            if give_up_on_end_edges and not shared and wanted >= edge_lengths[edge] - _TOLERANCE:
                return polycurve((curve,))  # Fillet Distance: does not fit an end edge, Grasshopper gives up
            allowed = min(allowed, edge_lengths[edge] / 2.0 if shared else edge_lengths[edge] * (1.0 - 1e-9))
        arcs[vertex] = _corner_arc(points[vertex], d_in, d_out, allowed)
    if all(arc is None for arc in arcs.values()):
        return polycurve((curve,))
    segments: list = []
    if closed:
        cycle = corners + [corners[0]]
        for a, b in zip(cycle, cycle[1:]):
            _append_fillet_run(segments, arcs, points, a, b, count)
    else:
        previous_point = points[0]
        for vertex in corners:
            arc = arcs[vertex]
            if arc is None:
                continue
            arc_start = curve_point_at(arc, 0.0)
            if distance(previous_point, arc_start) > _TOLERANCE:
                segments.append(AtomicLine(previous_point, arc_start))
            segments.append(arc)
            previous_point = curve_point_at(arc, 1.0)
        if distance(previous_point, points[-1]) > _TOLERANCE:
            segments.append(AtomicLine(previous_point, points[-1]))
    return polycurve(segments)


def _append_fillet_run(segments: list, arcs: dict, points, a: int, b: int, count: int) -> None:
    arc_a, arc_b = arcs[a], arcs[b]
    if arc_a is not None:
        segments.append(arc_a)
        from_point = curve_point_at(arc_a, 1.0)
    else:
        from_point = points[a]
    to_point = curve_point_at(arc_b, 0.0) if arc_b is not None else points[b]
    if distance(from_point, to_point) > _TOLERANCE:
        segments.append(AtomicLine(from_point, to_point))


# ── dash pattern ───────────────────────────────────────────────────


def dash_pattern(curve, pattern: Sequence[float]) -> tuple[list, list]:
    """Grasshopper's Dash Pattern: walk the curve by length, alternating dashes and gaps through the
    pattern (odd patterns swap roles every cycle); the last piece is cut at the curve end. Negative
    lengths raise; zero-length pieces are skipped."""
    values = [float(v) for v in pattern]
    if not values:
        return [], []
    if any(v < 0.0 for v in values):
        raise ValueError("Dash patterns cannot have negative length segments")
    if all(v <= _TOLERANCE for v in values):
        raise ValueError("Dash patterns need at least one positive length")
    total = curve_length(curve)
    dashes, gaps = [], []
    position, index, is_dash = 0.0, 0, True
    while position < total - _TOLERANCE * max(1.0, total):
        step = values[index % len(values)]
        stop = min(total, position + step)
        if stop - position > _TOLERANCE:
            piece = sub_curve(curve, curve_parameter_at_length(curve, position), curve_parameter_at_length(curve, stop))
            (dashes if is_dash else gaps).append(piece)
        position, index, is_dash = stop, index + 1, not is_dash
    return dashes, gaps


# ── blends ─────────────────────────────────────────────────────────


def _end_state(curve, at_end: bool) -> tuple[AtomicPoint, AtomicVector, AtomicVector]:
    start, end = curve_domain_of(curve)
    t = end if at_end else start
    point, first, _, _ = curve_derivatives_at(curve, t)
    return point, unit(first), _curvature_vector(curve, t)


def _bezier(points: Sequence[AtomicPoint]) -> AtomicNurbsCurve:
    degree = len(points) - 1
    bezier = AtomicNurbsCurve(tuple(points), (1.0,) * len(points), (0.0,) * (degree + 1) + (1.0,) * (degree + 1), degree)
    return redomain(bezier, 0.0, nurbs_curve_length(bezier, 1e-10))


def blend_points(p0: AtomicPoint, t0: AtomicVector, k0: AtomicVector, p1: AtomicPoint, t1: AtomicVector, k1: AtomicVector, bulge0: float, bulge1: float, continuity: int) -> list[AtomicPoint]:
    """Control points of Rhino's blend: a line (0), a cubic with handles ``bulge · chord`` (1) or a
    quintic with handles ``0.4 · bulge · chord`` and the curvature terms ``1.25 · κ · handle²`` (2)."""
    chord = distance(p0, p1)
    if int(continuity) <= 0:
        return [p0, p1]
    if int(continuity) == 1:
        return [p0, _move(p0, t0, bulge0 * chord), _move(p1, t1, -bulge1 * chord), p1]
    a, b = 0.4 * bulge0 * chord, 0.4 * bulge1 * chord
    return [
        p0,
        _move(p0, t0, a),
        _move(_move(p0, t0, 2.0 * a), k0, 1.25 * a * a),
        _move(_move(p1, t1, -2.0 * b), k1, 1.25 * b * b),
        _move(p1, t1, -b),
        p1,
    ]


def blend_curve(curve_a, curve_b, bulge_a: float, bulge_b: float, continuity: int):
    """Grasshopper's Blend Curve from the end of A to the start of B (continuity 0 gives a line, 1 a
    cubic, 2 — or anything else — a quintic); the NURBS domain is the blend's length."""
    p0, t0, k0 = _end_state(curve_a, True)
    p1, t1, k1 = _end_state(curve_b, False)
    level = int(continuity) if int(continuity) in (0, 1) else 2
    if level == 0:
        return AtomicLine(p0, p1)
    return _bezier(blend_points(p0, t0, k0, p1, t1, k1, float(bulge_a), float(bulge_b), level))


def blend_curve_through_point(curve_a, curve_b, point: AtomicPoint, continuity: int):
    """Grasshopper's Blend Curve Pt: the blend with equal bulges chosen so the curve passes through
    *point* (continuity 0 is treated as tangency, as Grasshopper does); raises when no bulge reaches it."""
    level = 1 if int(continuity) <= 1 else 2
    p0, t0, k0 = _end_state(curve_a, True)
    p1, t1, k1 = _end_state(curve_b, False)

    def curve_for(bulge: float) -> AtomicNurbsCurve:
        points = blend_points(p0, t0, k0, p1, t1, k1, bulge, bulge, level)
        degree = len(points) - 1
        return AtomicNurbsCurve(tuple(points), (1.0,) * len(points), (0.0,) * (degree + 1) + (1.0,) * (degree + 1), degree)

    def gap(bulge: float) -> float:
        return _point_curve_distance(curve_for(bulge), point)

    candidates = [0.01 * 1.1 ** i for i in range(120)]  # 0.01 … ~ 900
    best = min(candidates, key=gap)
    low, high = best / 1.1, best * 1.1
    for _ in range(80):
        m1, m2 = low + (high - low) * 0.381966, high - (high - low) * 0.381966
        if gap(m1) < gap(m2):
            high = m2
        else:
            low = m1
    bulge = 0.5 * (low + high)
    if gap(bulge) > 1e-6 * max(1.0, distance(p0, p1)):
        raise ValueError("Blend could not be fitted to point")
    return _bezier(blend_points(p0, t0, k0, p1, t1, k1, bulge, bulge, level))


def _point_curve_distance(curve: AtomicNurbsCurve, point: AtomicPoint, samples: int = 64) -> float:
    from pyhopper.Utils.Nurbs import curve_point

    start, end = curve_domain_of(curve)
    best_t = min((start + (end - start) * i / samples for i in range(samples + 1)), key=lambda t: distance(curve_point(curve, t), point))
    step = (end - start) / samples
    low, high = max(start, best_t - step), min(end, best_t + step)
    for _ in range(60):
        m1, m2 = low + (high - low) * 0.381966, high - (high - low) * 0.381966
        if distance(curve_point(curve, m1), point) < distance(curve_point(curve, m2), point):
            high = m2
        else:
            low = m1
    return distance(curve_point(curve, 0.5 * (low + high)), point)


def connect_curves(curves: Sequence, continuity: int, close: bool, bulge: float):
    """Grasshopper's Connect Curves: the curves in order with blends (see :func:`blend_curve`) between
    consecutive ends that do not touch, optionally closed with a blend back to the start."""
    items = list(curves)
    if not items:
        raise ValueError("Connect Curves needs at least one curve")
    if len(items) == 1 and not close:
        return items[0]
    segments: list = []
    for index, curve in enumerate(items):
        if index:
            previous_end, this_start = curve_endpoints(segments[-1])[1], curve_endpoints(curve)[0]
            if distance(previous_end, this_start) > JOIN_TOLERANCE:
                segments.append(blend_curve(segments[-1], curve, bulge, bulge, continuity))
        segments.append(curve)
    if close:
        last_end, first_start = curve_endpoints(segments[-1])[1], curve_endpoints(segments[0])[0]
        if distance(last_end, first_start) > JOIN_TOLERANCE:
            segments.append(blend_curve(segments[-1], segments[0], bulge, bulge, continuity))
    return polycurve(segments)


def tangent_curve(vertices: Sequence[AtomicPoint], tangents: Sequence[AtomicVector], blend: float, degree: int) -> tuple[AtomicNurbsCurve, float, AtomicInterval]:
    """Grasshopper's Tangent Curve: a clamped uniform B-spline (odd degree ≥ 3, even degrees are
    raised) whose control polygon runs from each vertex along its tangent by ``blend · chord``, with
    ``(degree − 1) / 2`` handle points per side; the knot domain is the curve length."""
    points, directions = list(vertices), list(tangents)
    if len(points) != len(directions):
        raise ValueError("You must supply equal numbers of points and tangents")
    if len(points) < 2:
        raise ValueError("Tangent Curve needs at least two vertices")
    p = max(3, int(degree))
    if p % 2 == 0:
        p += 1
    handles = (p - 1) // 2
    control: list[AtomicPoint] = [points[0]]
    for index in range(len(points) - 1):
        a, b = points[index], points[index + 1]
        ta, tb = unit(directions[index]), unit(directions[index + 1])
        h = float(blend) * distance(a, b)
        for j in range(1, handles + 1):
            control.append(_move(a, ta, h * j / handles))
        for j in range(handles, 0, -1):
            control.append(_move(b, tb, -h * j / handles))
        control.append(b)
    spans = len(control) - p
    knots = [0.0] * (p + 1) + [float(i) / spans for i in range(1, spans)] + [1.0] * (p + 1)
    curve = AtomicNurbsCurve(tuple(control), (1.0,) * len(control), tuple(knots), p)
    total = nurbs_curve_length(curve, 1e-10)
    curve = redomain(curve, 0.0, total)
    return curve, total, AtomicInterval(0.0, total)


def polyarc(vertices: Sequence[AtomicPoint], tangent: AtomicVector | None, closed: bool):
    """Grasshopper's PolyArc: arcs through consecutive vertices, each tangent to the previous one
    (the first to *tangent*; without a tangent, or when the tangent runs along the chord, the segment
    is a line); *closed* adds an equal-tangent biarc back to the start. Two vertices give the bare
    segment."""
    points = list(vertices)
    if len(points) < 2:
        raise ValueError("PolyArc needs at least two vertices")
    direction = None if tangent is None or is_zero(tangent, 1e-12) else unit(tangent)
    segments: list = []
    for a, b in zip(points, points[1:]):
        segment = _arc_from_tangent(a, b, direction)
        segments.append(segment)
        direction = curve_tangent_at(segment, 1.0)
    if closed and len(points) > 2:
        from pyhopper.Utils.Tangency import biarc

        first_direction = curve_tangent_at(segments[0], 0.0)
        start_point, end_point = points[-1], points[0]
        if length(cross(direction, first_direction)) <= 1e-12 and length(cross(direction, unit(sub(end_point, start_point)))) <= 1e-12:
            segments.append(AtomicLine(start_point, end_point))
        else:
            arc_a, arc_b, _ = biarc(start_point, direction, end_point, first_direction, 0.5)
            segments.append(AtomicPolyCurve((arc_a, arc_b), (natural_span(arc_a), natural_span(arc_b)), 0.0))
    if len(segments) == 1:
        return segments[0]
    return polycurve(segments)


def _arc_from_tangent(a: AtomicPoint, b: AtomicPoint, direction: AtomicVector | None):
    chord = sub(b, a)
    if direction is None or length(cross(direction, unit(chord))) <= 1e-9:
        return AtomicLine(a, b)
    lateral = sub(chord, scale(direction, dot(chord, direction)))
    normal_in_plane = unit(lateral)
    radius = dot(chord, chord) / (2.0 * dot(chord, normal_in_plane))
    centre = _move(a, normal_in_plane, radius)
    x_axis = unit(sub(a, centre))
    plane_normal = unit(cross(x_axis, direction))
    to_end = sub(b, centre)
    sweep = math.atan2(dot(cross(x_axis, to_end), plane_normal), dot(x_axis, to_end)) % (2.0 * math.pi)
    return AtomicArc(AtomicPlane(centre, plane_normal, x_axis), radius, AtomicInterval(0.0, sweep))
