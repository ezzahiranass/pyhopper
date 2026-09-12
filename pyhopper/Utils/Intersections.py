"""Intersections - curve|plane, curve|line, curve|curve, curve self, surface|line,
brep|plane sections, plane regions, contour planes and region trimming (the K4
kernel of the component roadmap), with the conventions read off Grasshopper 8.

Coincidence is judged with pyhopper's absolute tolerance (``Tolerances``);
intersection parameters are the atoms' own.
"""

from __future__ import annotations

import math
from typing import Callable, Sequence

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicLine,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyCurve,
    AtomicPolyline,
    AtomicRectangle,
    AtomicSurface,
    AtomicVector,
)
from pyhopper.Utils.ClosestPoints import _polygon_contains, brep_faces, surface_line_hits
from pyhopper.Utils.CurveOps import join_curves, shatter
from pyhopper.Utils.Curves import (
    curve_derivatives_at,
    curve_domain_of,
    curve_is_closed,
    curve_planarity,
    curve_point_at,
    interpolate_nurbs_curve,
    polycurve_breaks,
)
from pyhopper.Utils.Interpolation import CHORD, rhino_interpolated_curve
from pyhopper.Utils.Nurbs import surface_derivatives, surface_domain, surface_normal
from pyhopper.Utils.Planes import plane_coordinates, point_on_plane, project_point, signed_distance
from pyhopper.Utils.Tolerances import ABSOLUTE_TOLERANCE
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Utils.Vectors import cross, distance, dot, is_zero, length, scale, sub, unit

_ZERO = 1e-12


# ── sampling ───────────────────────────────────────────────────────


def _sample_parameters(curve, per_span: int = 24) -> list[float]:
    """Parameters dense enough to catch every crossing: polyline vertices exactly, ``per_span``
    steps per knot span otherwise."""
    start, end = curve_domain_of(curve)
    if isinstance(curve, AtomicLine):
        return [0.0, 1.0]
    if isinstance(curve, (AtomicPolyline, AtomicRectangle)):
        count = len(curve.points) - 1 if isinstance(curve, AtomicPolyline) else 4
        return [i / count for i in range(count + 1)]
    if isinstance(curve, AtomicPolyCurve):
        parameters: list[float] = []
        breaks = polycurve_breaks(curve)
        for index, segment in enumerate(curve.segments):
            seg_start, seg_end = curve_domain_of(segment)
            for t in _sample_parameters(segment, per_span):
                local = 0.0 if seg_end - seg_start <= _ZERO else (t - seg_start) / (seg_end - seg_start)
                value = breaks[index] + (breaks[index + 1] - breaks[index]) * local
                if not parameters or value > parameters[-1] + 1e-12:
                    parameters.append(value)
        return parameters
    nurbs = as_nurbs_curve(curve)
    spans = max(1, len(nurbs.control_points) - int(nurbs.degree))
    steps = per_span * spans
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        steps = max(steps, 64)
    return [start + (end - start) * i / steps for i in range(steps + 1)]


def _polyline_samples(curve, per_span: int = 24) -> list[tuple[float, AtomicPoint]]:
    return [(t, curve_point_at(curve, t)) for t in _sample_parameters(curve, per_span)]


# ── curve | plane ──────────────────────────────────────────────────


def _bisect_root(function: Callable[[float], float], a: float, b: float, fa: float, iterations: int = 80) -> float:
    for _ in range(iterations):
        middle = 0.5 * (a + b)
        fm = function(middle)
        if fm == 0.0 or abs(b - a) <= 1e-15 * max(1.0, abs(a), abs(b)):
            return middle
        if (fm < 0) == (fa < 0):
            a, fa = middle, fm
        else:
            b = middle
    return 0.5 * (a + b)


def _minimise(function: Callable[[float], float], a: float, b: float, iterations: int = 80) -> float:
    for _ in range(iterations):
        m1, m2 = a + (b - a) * 0.381966, b - (b - a) * 0.381966
        if function(m1) < function(m2):
            b = m2
        else:
            a = m1
    return 0.5 * (a + b)


def _roots_of(function: Callable[[float], float], parameters: Sequence[float], tolerance: float) -> list[float]:
    """Roots (and touches within *tolerance*) of a sampled scalar function; runs where the function stays
    within tolerance report their two ends (Rhino's overlap events)."""
    values = [function(t) for t in parameters]
    roots: list[float] = []
    index = 0
    while index < len(parameters) - 1:
        t0, t1, f0, f1 = parameters[index], parameters[index + 1], values[index], values[index + 1]
        if abs(f0) <= tolerance and abs(f1) <= tolerance:
            # an overlap run: report its ends
            end = index + 1
            while end < len(parameters) - 1 and abs(values[end + 1]) <= tolerance:
                end += 1
            roots.append(_refine_run_end(function, parameters, values, index, tolerance, backwards=True))
            roots.append(_refine_run_end(function, parameters, values, end, tolerance, backwards=False))
            index = end
            continue
        if abs(f0) <= tolerance and (index == 0 or abs(values[index - 1]) > tolerance):
            roots.append(t0 if f0 == 0.0 else _snap(function, t0, t1, tolerance))
        elif (f0 < 0) != (f1 < 0) and abs(f0) > tolerance and abs(f1) > tolerance:
            roots.append(_bisect_root(function, t0, t1, f0))
        elif abs(f0) > tolerance and abs(f1) > tolerance and (f0 < 0) == (f1 < 0):
            # both away from zero on the same side: a tangential touch may hide between the samples
            if index + 2 < len(parameters):
                pass
            t_min = _minimise(lambda t: abs(function(t)), t0, t1, 40)
            if abs(function(t_min)) <= tolerance and t0 + 1e-9 < t_min < t1 - 1e-9:
                roots.append(t_min)
        index += 1
    last_t, last_f = parameters[-1], values[-1]
    if abs(last_f) <= tolerance and abs(values[-2]) > tolerance:
        roots.append(last_t if last_f == 0.0 else _snap(function, last_t, parameters[-2], tolerance))
    merged: list[float] = []
    for t in sorted(roots):
        if not merged or t - merged[-1] > 1e-9 * max(1.0, abs(parameters[-1] - parameters[0])):
            merged.append(t)
    return merged


def _snap(function, t, neighbour, tolerance) -> float:
    """A sample within tolerance of zero: move to the exact zero if the sign changes towards the neighbour."""
    f0, f1 = function(t), function(neighbour)
    if f0 != 0.0 and f1 != 0.0 and (f0 < 0) != (f1 < 0):
        return _bisect_root(function, t, neighbour, f0)
    return t


def _refine_run_end(function, parameters, values, index, tolerance, backwards: bool) -> float:
    """Where a within-tolerance run begins (``backwards``) or ends: the exact zero if the function
    crosses zero towards the neighbouring sample, else the sample itself."""
    t = parameters[index]
    neighbour_index = index - 1 if backwards else index + 1
    if 0 <= neighbour_index < len(parameters):
        f0, f1 = values[index], values[neighbour_index]
        if f0 != 0.0 and f1 != 0.0 and (f0 < 0) != (f1 < 0):
            return _bisect_root(function, t, parameters[neighbour_index], f0)
    return t


def curve_plane_intersections(curve, plane: AtomicPlane, tolerance: float = ABSOLUTE_TOLERANCE, seam_twice: bool = False) -> list[tuple[float, AtomicPoint]]:
    """Parameters and points where the curve meets the plane, sorted by parameter: crossings, touches
    within *tolerance* and the two ends of any stretch lying in the plane (Rhino's overlap events).
    ``seam_twice`` also reports a crossing at a closed curve's seam at its end parameter."""
    if isinstance(curve, AtomicLine):
        roots = _segment_plane_roots([curve.start, curve.end], plane, tolerance)
        return [(t, curve_point_at(curve, t)) for t in roots]
    if isinstance(curve, (AtomicPolyline, AtomicRectangle)):
        polyline = curve if isinstance(curve, AtomicPolyline) else AtomicPolyline(as_nurbs_curve(curve).control_points)
        count = len(polyline.points) - 1
        roots: list[float] = []
        for index, (a, b) in enumerate(zip(polyline.points, polyline.points[1:])):
            for local in _segment_plane_roots([a, b], plane, tolerance):
                roots.append((index + local) / count)
        return _finish(curve, _merge_parameters(roots, 1.0), seam_twice)
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        return _finish(curve, _arc_plane_roots(curve, plane, tolerance), seam_twice)
    parameters = _sample_parameters(curve)
    roots = _roots_of(lambda t: signed_distance(plane, curve_point_at(curve, t)), parameters, tolerance)
    start, end = curve_domain_of(curve)
    return _finish(curve, _merge_parameters(roots, end - start), seam_twice)


def _finish(curve, roots: list[float], seam_twice: bool) -> list[tuple[float, AtomicPoint]]:
    """A closed curve's seam is one event, reported at the start parameter (Rhino), unless ``seam_twice``
    asks for the end parameter as well (Curve Contour)."""
    start, end = curve_domain_of(curve)
    if roots and curve_is_closed(curve):
        eps = 1e-9 * max(1.0, abs(end - start))
        at_start, at_end = abs(roots[0] - start) <= eps, abs(roots[-1] - end) <= eps
        if at_end and not seam_twice:
            roots = ([] if at_start else [start]) + roots[:-1]
        elif seam_twice and at_start != at_end:
            roots = roots + [end] if at_start else [start] + roots
    return [(t, curve_point_at(curve, t)) for t in roots]


def _merge_parameters(roots: Sequence[float], extent: float) -> list[float]:
    merged: list[float] = []
    for t in sorted(roots):
        if not merged or t - merged[-1] > 1e-9 * max(1.0, extent):
            merged.append(t)
    return merged


def _segment_plane_roots(points, plane: AtomicPlane, tolerance: float) -> list[float]:
    a, b = points
    ha, hb = signed_distance(plane, a), signed_distance(plane, b)
    if abs(ha) <= tolerance and abs(hb) <= tolerance:
        return [0.0, 1.0]  # the segment lies in the plane: both ends
    if abs(ha) <= tolerance:
        return [0.0]
    if abs(hb) <= tolerance:
        return [1.0]
    if (ha < 0) == (hb < 0):
        return []
    return [ha / (ha - hb)]


def _arc_plane_roots(curve, plane: AtomicPlane, tolerance: float) -> list[float]:
    """Solve ``h(θ) = a cos θ + b sin θ + c = 0`` on the arc, with touches and coplanar arcs."""
    centre, x_axis = curve.plane.origin, curve.plane.x_axis
    y_axis = cross(curve.plane.normal, x_axis)
    radius = float(curve.radius)
    n = plane.normal
    a, b = radius * dot(x_axis, n), radius * dot(y_axis, n)
    c = signed_distance(plane, centre)
    amplitude = math.hypot(a, b)
    if isinstance(curve, AtomicCircle):
        angle_start, sweep = 0.0, 2.0 * math.pi
    else:
        angle_start, sweep = float(curve.angle.start), float(curve.angle.length)

    def parameter(angle: float) -> float | None:
        rel = (angle - angle_start) % (2.0 * math.pi) if sweep > 0 else (angle_start - angle) % (2.0 * math.pi)
        if rel <= abs(sweep) + 1e-12:
            return min(1.0, rel / abs(sweep))
        return None

    if amplitude <= _ZERO:
        return [0.0, 1.0] if abs(c) <= tolerance else []  # coplanar arc: both ends
    phase = math.atan2(b, a)
    if abs(c) > amplitude + tolerance:
        return []
    roots: list[float] = []
    if abs(abs(c) - amplitude) <= tolerance:
        # a touch: cos(θ - φ) = -c / amplitude at ±1
        angle = phase + (math.pi if c > 0 else 0.0)
        t = parameter(angle)
        if t is not None:
            roots.append(t)
    else:
        delta = math.acos(max(-1.0, min(1.0, -c / amplitude)))
        for angle in (phase + delta, phase - delta):
            t = parameter(angle)
            if t is not None:
                roots.append(t)
    for t_end in (0.0, 1.0):
        if abs(signed_distance(plane, curve_point_at(curve, t_end))) <= tolerance and all(abs(t_end - t) > 1e-9 for t in roots):
            roots.append(t_end)
    return _merge_parameters(roots, 1.0)


# ── curve | curve ──────────────────────────────────────────────────


def _segment_pair_distance(a0, a1, b0, b1) -> float:
    """Distance between two 3D segments (closest approach)."""
    d1, d2 = sub(a1, a0), sub(b1, b0)
    r = sub(a0, b0)
    aa, bb, cc, dd, ee = dot(d1, d1), dot(d1, d2), dot(d2, d2), dot(d1, r), dot(d2, r)
    denominator = aa * cc - bb * bb
    if denominator <= 1e-14 * max(1.0, aa * cc):
        s = 0.0
        t = ee / cc if cc > _ZERO else 0.0
    else:
        s = (bb * ee - cc * dd) / denominator
        t = (aa * ee - bb * dd) / denominator
    s, t = min(1.0, max(0.0, s)), min(1.0, max(0.0, t))
    # re-clamp the other parameter for the clamped one
    if cc > _ZERO:
        t = min(1.0, max(0.0, (bb * s + ee) / cc))
    if aa > _ZERO:
        s = min(1.0, max(0.0, (bb * t - dd) / aa))
    pa = AtomicPoint(a0.x + d1.x * s, a0.y + d1.y * s, a0.z + d1.z * s)
    pb = AtomicPoint(b0.x + d2.x * t, b0.y + d2.y * t, b0.z + d2.z * t)
    return distance(pa, pb)


def _gauss_newton_pair(curve_a, curve_b, ta: float, tb: float, mapper: Callable[[AtomicPoint], AtomicPoint] | None = None) -> tuple[float, float]:
    """Refine an approximate crossing by Gauss-Newton on ``|A(ta) - B(tb)|²`` (points mapped through
    *mapper* when intersecting in a projection); parameters are clamped to the domains."""
    a0, a1 = curve_domain_of(curve_a)
    b0, b1 = curve_domain_of(curve_b)
    for _ in range(50):
        pa, da, _, _ = curve_derivatives_at(curve_a, ta)
        pb, db, _, _ = curve_derivatives_at(curve_b, tb)
        if mapper is not None:
            pa, pb = mapper(pa), mapper(pb)
            da, db = _map_vector(mapper, da), _map_vector(mapper, db)
        residual = sub(pa, pb)
        j11, j12, j22 = dot(da, da), -dot(da, db), dot(db, db)
        g1, g2 = dot(da, residual), -dot(db, residual)
        det = j11 * j22 - j12 * j12
        if abs(det) <= 1e-18 * max(1.0, j11 * j22):
            break
        step_a = (g1 * j22 - g2 * j12) / det
        step_b = (j11 * g2 - j12 * g1) / det
        ta_new, tb_new = min(a1, max(a0, ta - step_a)), min(b1, max(b0, tb - step_b))
        moved = abs(ta_new - ta) + abs(tb_new - tb)
        ta, tb = ta_new, tb_new
        if moved <= 1e-15 * max(1.0, abs(a1 - a0), abs(b1 - b0)):
            break
    return ta, tb


def _map_vector(mapper, vector: AtomicVector) -> AtomicVector:
    origin = mapper(AtomicPoint(0.0, 0.0, 0.0))
    moved = mapper(AtomicPoint(vector.x, vector.y, vector.z))
    return AtomicVector(moved.x - origin.x, moved.y - origin.y, moved.z - origin.z)


def _collinear_overlap(a0, a1, b0, b1, tolerance: float):
    """Overlap of two collinear segments as parameter pairs ``[(sa, sb), (sa, sb)]`` (local 0..1)."""
    d = sub(a1, a0)
    la = length(d)
    if la <= _ZERO:
        return None
    axis = scale(d, 1.0 / la)
    for p in (b0, b1):
        if length(cross(sub(p, a0), axis)) > tolerance:
            return None
    sb0, sb1 = dot(sub(b0, a0), axis) / la, dot(sub(b1, a0), axis) / la
    lo, hi = max(0.0, min(sb0, sb1)), min(1.0, max(sb0, sb1))
    if hi - lo <= 1e-9:
        return None
    lb = length(sub(b1, b0))
    if lb <= _ZERO:
        return None

    def b_param(s):
        p = AtomicPoint(a0.x + d.x * s, a0.y + d.y * s, a0.z + d.z * s)
        return dot(sub(p, b0), sub(b1, b0)) / (lb * lb)

    return [(lo, b_param(lo)), (hi, b_param(hi))]


def curve_curve_intersections(curve_a, curve_b, tolerance: float = ABSOLUTE_TOLERANCE, plane: AtomicPlane | None = None, overlap_ends: bool = True) -> list[tuple[float, float, AtomicPoint]]:
    """``(t_a, t_b, point)`` for every place the curves meet within *tolerance* (crossings and touches;
    a collinear overlap of straight pieces reports its two ends, or only its start along A when
    ``overlap_ends`` is off), sorted along curve A. The point is the midpoint of the two curve points,
    as Grasshopper reports it. With *plane* the test runs in the projection onto that plane (Trim with
    Region). Straight pieces against arcs and circles are solved in closed form (exact touches);
    everything else by sampling and Gauss-Newton refinement."""
    mapper = (lambda point: project_point(plane, point)) if plane is not None else None
    straight_a, straight_b = isinstance(curve_a, (AtomicLine, AtomicPolyline)), isinstance(curve_b, (AtomicLine, AtomicPolyline))
    circular_a, circular_b = isinstance(curve_a, (AtomicArc, AtomicCircle)), isinstance(curve_b, (AtomicArc, AtomicCircle))
    if straight_a and circular_b:
        analytic = _straight_circular_events(curve_a, curve_b, tolerance, plane)
        if analytic is not None:
            return _dedupe_pairs(analytic, curve_a, curve_b)
    if circular_a and straight_b:
        analytic = _straight_circular_events(curve_b, curve_a, tolerance, plane)
        if analytic is not None:
            return _dedupe_pairs([(tb, ta, point) for ta, tb, point in analytic], curve_a, curve_b)
    samples_a = _polyline_samples(curve_a)
    samples_b = _polyline_samples(curve_b)
    if mapper is not None:
        samples_a = [(t, mapper(p)) for t, p in samples_a]
        samples_b = [(t, mapper(p)) for t, p in samples_b]
    slack = tolerance + 0.0
    results: list[tuple[float, float, AtomicPoint, float]] = []
    overlap_starts: list[AtomicPoint] = []
    overlap_stops: list[AtomicPoint] = []
    for i in range(len(samples_a) - 1):
        (ta0, pa0), (ta1, pa1) = samples_a[i], samples_a[i + 1]
        reach = distance(pa0, pa1)
        for j in range(len(samples_b) - 1):
            (tb0, pb0), (tb1, pb1) = samples_b[j], samples_b[j + 1]
            if _segment_pair_distance(pa0, pa1, pb0, pb1) > slack + 0.5 * (reach + distance(pb0, pb1)):
                continue
            if straight_a and straight_b:
                overlap = _collinear_overlap(pa0, pa1, pb0, pb1, tolerance)
                if overlap is not None:
                    for index, (sa, sb) in enumerate(overlap):
                        ta, tb = ta0 + (ta1 - ta0) * sa, tb0 + (tb1 - tb0) * sb
                        point = _midpoint(curve_a, curve_b, ta, tb)
                        (overlap_starts if index == 0 else overlap_stops).append(point)
                        if index == 0 or overlap_ends:
                            results.append((ta, tb, point, 0.0))
                    continue
            ta, tb = _gauss_newton_pair(curve_a, curve_b, 0.5 * (ta0 + ta1), 0.5 * (tb0 + tb1), mapper)
            pa, pb = curve_point_at(curve_a, ta), curve_point_at(curve_b, tb)
            if mapper is not None:
                pa, pb = mapper(pa), mapper(pb)
            residual = distance(pa, pb)
            if residual <= tolerance:
                results.append((ta, tb, _midpoint(curve_a, curve_b, ta, tb), residual))
    if not overlap_ends and overlap_stops:
        # Rhino folds a touch at the end of an overlap into the overlap event: drop it with the end
        results = [
            event for event in results
            if any(distance(event[2], p) <= tolerance for p in overlap_starts) or all(distance(event[2], p) > tolerance for p in overlap_stops)
        ]
    return _dedupe_pairs(_cluster_events(results, tolerance), curve_a, curve_b)


def _straight_pieces(curve) -> list[tuple[float, float, AtomicPoint, AtomicPoint]]:
    if isinstance(curve, AtomicLine):
        return [(0.0, 1.0, curve.start, curve.end)]
    count = len(curve.points) - 1
    return [(i / count, (i + 1) / count, a, b) for i, (a, b) in enumerate(zip(curve.points, curve.points[1:]))]


def _straight_circular_events(straight, circular, tolerance: float, plane: AtomicPlane | None):
    """Closed-form events between a line/polyline and an arc/circle lying in one plane (or seen in the
    projection onto *plane*); None when the configuration is not planar, leaving it to the solver."""
    circle_plane = circular.plane
    if plane is not None:
        if abs(abs(dot(unit(plane.normal), unit(circle_plane.normal))) - 1.0) > 1e-9:
            return None
        circle_plane = AtomicPlane(project_point(plane, circle_plane.origin), circle_plane.normal, circle_plane.x_axis)
    radius = float(circular.radius)
    if isinstance(circular, AtomicCircle):
        angle_start, sweep = 0.0, 2.0 * math.pi
    else:
        angle_start, sweep = float(circular.angle.start), float(circular.angle.length)

    def parameter(angle: float) -> float | None:
        rel = (angle - angle_start) % (2.0 * math.pi) if sweep > 0 else (angle_start - angle) % (2.0 * math.pi)
        if rel <= abs(sweep) + 1e-9:
            return min(1.0, rel / abs(sweep))
        if 2.0 * math.pi - rel <= tolerance / max(radius, _ZERO):
            return 0.0  # within tolerance of the arc's start, coming around
        return None

    def event(t0, t1, q0, dq, s):
        s = min(1.0, max(0.0, s))
        x, y = q0[0] + dq[0] * s, q0[1] + dq[1] * s
        tb = parameter(math.atan2(y, x))
        if tb is None:
            return None
        ta = t0 + (t1 - t0) * s
        pa, pb = curve_point_at(straight, ta), curve_point_at(circular, tb)
        if plane is not None:
            pa, pb = project_point(plane, pa), project_point(plane, pb)
        if distance(pa, pb) > tolerance:
            return None
        return (ta, tb, _midpoint(straight, circular, ta, tb))

    results = []
    for t0, t1, a, b in _straight_pieces(straight):
        if plane is not None:
            a, b = project_point(plane, a), project_point(plane, b)
        heights = (signed_distance(circle_plane, a), signed_distance(circle_plane, b))
        if plane is None and max(abs(h) for h in heights) > tolerance:
            return None  # a skew segment: let the solver judge it
        q0 = plane_coordinates(circle_plane, a)[:2]
        q1 = plane_coordinates(circle_plane, b)[:2]
        dq = (q1[0] - q0[0], q1[1] - q0[1])
        aa = dq[0] * dq[0] + dq[1] * dq[1]
        if aa <= _ZERO:
            continue
        bb = 2.0 * (q0[0] * dq[0] + q0[1] * dq[1])
        cc = q0[0] * q0[0] + q0[1] * q0[1] - radius * radius
        discriminant = bb * bb - 4.0 * aa * cc
        s_foot = -bb / (2.0 * aa)
        foot_distance = math.hypot(q0[0] + dq[0] * s_foot, q0[1] + dq[1] * s_foot)
        candidates: list[float] = []
        if discriminant <= 0.0 or math.sqrt(discriminant / aa) <= tolerance:  # no chord, or one shorter than the tolerance
            if abs(foot_distance - radius) <= tolerance:
                candidates.append(s_foot)  # a touch
        else:
            root = math.sqrt(discriminant)
            candidates.extend(((-bb - root) / (2.0 * aa), (-bb + root) / (2.0 * aa)))
        reach = math.sqrt(aa)
        for s in candidates:
            if -tolerance / reach <= s <= 1.0 + tolerance / reach:
                found = event(t0, t1, q0, dq, s)
                if found is not None:
                    results.append(found)
    return results


def _cluster_events(results, tolerance: float) -> list[tuple[float, float, AtomicPoint]]:
    """A tangential touch converges to a whole stretch of points within tolerance; keep one event per
    cluster of mutually close points — the one where the curves actually come closest."""
    clusters: list[list[tuple[float, float, AtomicPoint, float]]] = []
    for event in sorted(results, key=lambda item: (item[0], item[1])):
        for cluster in clusters:
            if any(distance(event[2], other[2]) <= tolerance for other in cluster):
                cluster.append(event)
                break
        else:
            clusters.append([event])
    return [min(cluster, key=lambda item: item[3])[:3] for cluster in clusters]


def _midpoint(curve_a, curve_b, ta, tb) -> AtomicPoint:
    pa, pb = curve_point_at(curve_a, ta), curve_point_at(curve_b, tb)
    return AtomicPoint(0.5 * (pa.x + pb.x), 0.5 * (pa.y + pb.y), 0.5 * (pa.z + pb.z))


def _dedupe_pairs(results, curve_a, curve_b):
    """Sort along curve A and drop repeats; a closed curve's seam counts once, at its start parameter."""
    a0, a1 = curve_domain_of(curve_a)
    b0, b1 = curve_domain_of(curve_b)
    tol_a, tol_b = 1e-7 * max(1.0, abs(a1 - a0)), 1e-7 * max(1.0, abs(b1 - b0))
    if curve_is_closed(curve_a):
        results = [(a0 if abs(ta - a1) <= tol_a else ta, tb, p) for ta, tb, p in results]
    if curve_is_closed(curve_b):
        results = [(ta, b0 if abs(tb - b1) <= tol_b else tb, p) for ta, tb, p in results]
    unique: list[tuple[float, float, AtomicPoint]] = []
    for ta, tb, p in sorted(results, key=lambda item: (item[0], item[1])):
        if any(abs(ta - ua) <= tol_a and abs(tb - ub) <= tol_b for ua, ub, _ in unique):
            continue
        unique.append((ta, tb, p))
    return unique


def curve_self_intersections(curve, tolerance: float = ABSOLUTE_TOLERANCE) -> list[tuple[float, float, AtomicPoint]]:
    """Self-intersections as ``(t_first, t_second, point)`` pairs (non-adjacent stretches of the sampled
    curve that meet within *tolerance*), sorted by the first parameter."""
    samples = _polyline_samples(curve, 32)
    start, end = curve_domain_of(curve)
    closed = curve_is_closed(curve)
    count = len(samples) - 1
    results: list[tuple[float, float, AtomicPoint, float]] = []
    for i in range(count):
        (ta0, pa0), (ta1, pa1) = samples[i], samples[i + 1]
        for j in range(i + 2, count):
            if closed and i == 0 and j == count - 1:
                continue
            (tb0, pb0), (tb1, pb1) = samples[j], samples[j + 1]
            if _segment_pair_distance(pa0, pa1, pb0, pb1) > tolerance + 0.5 * (distance(pa0, pa1) + distance(pb0, pb1)):
                continue
            ta, tb = _gauss_newton_pair(curve, curve, 0.5 * (ta0 + ta1), 0.5 * (tb0 + tb1))
            eps = 1e-6 * max(1.0, abs(end - start))
            if abs(ta - tb) <= eps:
                continue
            if closed and abs(min(ta, tb) - start) <= eps and abs(max(ta, tb) - end) <= eps:
                continue  # the seam is not a self-intersection
            residual = distance(curve_point_at(curve, ta), curve_point_at(curve, tb))
            if residual <= tolerance:
                results.append((min(ta, tb), max(ta, tb), _midpoint(curve, curve, ta, tb), residual))
    return _dedupe_pairs(_cluster_events(results, tolerance), curve, curve)


def curve_line_intersections(curve, line: AtomicLine, tolerance: float = ABSOLUTE_TOLERANCE) -> list[tuple[float, AtomicPoint]]:
    """Points where the curve meets the *infinite* line through the segment, within tolerance, sorted by
    curve parameter (the point on the curve)."""
    from pyhopper.Utils.Bounds import geometry_extents
    from pyhopper.Utils.Planes import plane_from_normal

    direction = sub(line.end, line.start)
    if is_zero(direction):
        raise ValueError("The line has no direction")
    axis = unit(direction)
    # a segment just covering the curve's reach along the line keeps the arithmetic well scaled
    low, high = geometry_extents(curve, plane_from_normal(line.start, axis))[2]
    margin = 2.0 * tolerance + 1e-6 * max(1.0, high - low)
    long_line = AtomicLine(_along(line.start, axis, low - margin), _along(line.start, axis, high + margin))
    return [(ta, curve_point_at(curve, ta)) for ta, _, _ in curve_curve_intersections(curve, long_line, tolerance)]


# ── surfaces and breps ─────────────────────────────────────────────


def surface_line_intersections(surface: AtomicSurface, line: AtomicLine) -> list[tuple[float, float, AtomicPoint, AtomicVector, float]]:
    """``(u, v, point, unit normal, line parameter)`` for every place the infinite line through the
    segment pierces the surface, ordered along the line."""
    direction = sub(line.end, line.start)
    if is_zero(direction):
        raise ValueError("The line has no direction")
    hits = surface_line_hits(surface, line.start, direction)
    results = []
    for u, v, s, point in hits:
        results.append((u, v, point, surface_normal(surface, u, v), s / length(direction)))
    return results


def surface_line_overlaps(surface: AtomicSurface, line: AtomicLine, tolerance: float = ABSOLUTE_TOLERANCE) -> list[AtomicLine]:
    """Stretches of the infinite line through the segment that lie in a planar face (Rhino's overlap
    events), ordered along the line; empty for curved faces or a line off the face's plane."""
    direction = sub(line.end, line.start)
    if is_zero(direction):
        raise ValueError("The line has no direction")
    plane = _face_is_planar(surface)
    if plane is None:
        return []
    axis = unit(direction)
    if abs(dot(axis, plane.normal)) > 1e-9 or abs(signed_distance(plane, line.start)) > tolerance:
        return []
    boundary = [plane_coordinates(plane, p)[:2] for p in _face_boundary(surface, steps=16).points]
    x0, y0 = plane_coordinates(plane, line.start)[:2]
    dx, dy = plane_coordinates(AtomicPlane(AtomicPoint(0.0, 0.0, 0.0), plane.normal, plane.x_axis), AtomicPoint(axis.x, axis.y, axis.z))[:2]
    params: list[float] = []
    for (ax, ay), (bx, by) in zip(boundary, boundary[1:]):
        ex, ey = bx - ax, by - ay
        denominator = dx * ey - dy * ex
        if abs(denominator) <= _ZERO:
            continue
        f = (dy * (ax - x0) - dx * (ay - y0)) / denominator  # along the boundary edge
        if -1e-9 <= f <= 1.0 + 1e-9:
            params.append(((ax - x0) * ey - (ay - y0) * ex) / denominator)  # along the line
    params = _merge_parameters(params, max(abs(t) for t in params) if params else 1.0)
    overlaps: list[AtomicLine] = []
    for s0, s1 in zip(params, params[1:]):
        if s1 - s0 <= tolerance:
            continue
        mid = 0.5 * (s0 + s1)
        mx, my = x0 + dx * mid, y0 + dy * mid
        if _polygon_contains(boundary[:-1], mx, my) or _polygon_distance(boundary, mx, my) <= tolerance:
            overlaps.append(AtomicLine(_along(line.start, axis, s0), _along(line.start, axis, s1)))
    return overlaps


def _polygon_distance(polygon, x: float, y: float) -> float:
    best = math.inf
    for (ax, ay), (bx, by) in zip(polygon, polygon[1:]):
        ex, ey = bx - ax, by - ay
        extent = ex * ex + ey * ey
        f = 0.0 if extent <= _ZERO else max(0.0, min(1.0, ((x - ax) * ex + (y - ay) * ey) / extent))
        best = min(best, math.hypot(x - ax - ex * f, y - ay - ey * f))
    return best


def _along(origin: AtomicPoint, axis: AtomicVector, s: float) -> AtomicPoint:
    return AtomicPoint(origin.x + axis.x * s, origin.y + axis.y * s, origin.z + axis.z * s)


def _face_is_planar(surface: AtomicSurface) -> AtomicPlane | None:
    poles = [p for row in surface.poles for p in row]
    (u0, u1), (v0, v1) = surface_domain(surface)
    normal = surface_normal(surface, 0.5 * (u0 + u1), 0.5 * (v0 + v1))
    origin = poles[0]
    if all(abs(dot(sub(p, origin), normal)) <= 1e-9 * max(1.0, distance(p, origin)) for p in poles):
        return AtomicPlane(origin, normal, unit(sub(poles[1], poles[0])) if distance(poles[1], poles[0]) > _ZERO else surface.poles[1][0])
    return None


def _face_boundary(surface: AtomicSurface, steps: int = 8) -> AtomicPolyline:
    (u0, u1), (v0, v1) = surface_domain(surface)
    corners = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    points = []
    for (ua, va), (ub, vb) in zip(corners, corners[1:] + corners[:1]):
        for k in range(steps):
            f = k / steps
            points.append(surface_derivatives(surface, ua + (ub - ua) * f, va + (vb - va) * f, 1).point)
    points.append(points[0])
    return AtomicPolyline(tuple(points))


def surface_plane_section(surface: AtomicSurface, plane: AtomicPlane, tolerance: float = ABSOLUTE_TOLERANCE) -> list:
    """Curves where the plane cuts the surface: exact lines for planar faces (a coplanar face returns its
    boundary), otherwise marching squares on the parameter grid refined onto the plane and interpolated
    (straight sections become lines, closed loops periodic curves)."""
    (u0, u1), (v0, v1) = surface_domain(surface)
    face_plane = _face_is_planar(surface)
    if face_plane is not None:
        heights = [signed_distance(plane, p) for row in surface.poles for p in row]
        if all(abs(h) <= tolerance for h in heights):
            corners = [surface_derivatives(surface, u, v, 1).point for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
            return [AtomicPolyline(tuple(corners + [corners[0]]))]
    grid_u = max(24, 8 * max(1, len(surface.poles[0]) - int(surface.u_degree)))
    grid_v = max(24, 8 * max(1, len(surface.poles) - int(surface.v_degree)))
    us = [u0 + (u1 - u0) * i / grid_u for i in range(grid_u + 1)]
    vs = [v0 + (v1 - v0) * j / grid_v for j in range(grid_v + 1)]
    heights = [[signed_distance(plane, surface_derivatives(surface, u, v, 1).point) for v in vs] for u in us]
    if all(abs(h) > tolerance for row in heights for h in row) and all((h > 0) == (heights[0][0] > 0) for row in heights for h in row):
        return []
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for i in range(grid_u):
        for j in range(grid_v):
            cell = [(us[i], vs[j], heights[i][j]), (us[i + 1], vs[j], heights[i + 1][j]), (us[i + 1], vs[j + 1], heights[i + 1][j + 1]), (us[i], vs[j + 1], heights[i][j + 1])]
            crossings = []
            for (ua, va, ha), (ub, vb, hb) in zip(cell, cell[1:] + cell[:1]):
                if (ha < 0) != (hb < 0):
                    f = ha / (ha - hb)
                    crossings.append((ua + (ub - ua) * f, va + (vb - va) * f))
            if len(crossings) == 2:
                segments.append((crossings[0], crossings[1]))
            elif len(crossings) == 4:
                segments.append((crossings[0], crossings[1]))
                segments.append((crossings[2], crossings[3]))
    chains = _chain_segments(segments, 1e-9 * max(u1 - u0, v1 - v0))
    curves = []
    for chain in chains:
        points = [_refine_onto_plane(surface, plane, u, v) for u, v in chain]
        cleaned: list[AtomicPoint] = []
        for p in points:
            if not cleaned or distance(cleaned[-1], p) > 1e-9:
                cleaned.append(p)
        if len(cleaned) < 2:
            continue
        curves.append(_fit_section(cleaned, closed=distance(cleaned[0], cleaned[-1]) <= 1e-6 and len(cleaned) > 3))
    return curves


def _refine_onto_plane(surface, plane, u, v) -> AtomicPoint:
    (u0, u1), (v0, v1) = surface_domain(surface)
    for _ in range(30):
        ders = surface_derivatives(surface, u, v, 1)
        h = signed_distance(plane, ders.point)
        gu, gv = dot(ders.du, plane.normal), dot(ders.dv, plane.normal)
        norm = gu * gu + gv * gv
        if norm <= _ZERO or abs(h) <= 1e-13:
            break
        u = min(u1, max(u0, u - h * gu / norm))
        v = min(v1, max(v0, v - h * gv / norm))
    return surface_derivatives(surface, u, v, 1).point


def _chain_segments(segments, tolerance: float) -> list[list[tuple[float, float]]]:
    remaining = [list(segment) for segment in segments]
    chains: list[list[tuple[float, float]]] = []

    def same(a, b):
        return abs(a[0] - b[0]) <= tolerance and abs(a[1] - b[1]) <= tolerance

    while remaining:
        chain = remaining.pop(0)
        grown = True
        while grown:
            grown = False
            for index, segment in enumerate(remaining):
                a, b = segment
                if same(chain[-1], a):
                    chain.append(b)
                elif same(chain[-1], b):
                    chain.append(a)
                elif same(chain[0], b):
                    chain.insert(0, a)
                elif same(chain[0], a):
                    chain.insert(0, b)
                else:
                    continue
                remaining.pop(index)
                grown = True
                break
        chains.append(chain)
    return chains


def _fit_section(points: list[AtomicPoint], closed: bool):
    if closed:
        points = points[:-1]
    direction = sub(points[-1], points[0])
    if not closed and length(direction) > _ZERO and all(length(cross(sub(p, points[0]), unit(direction))) <= 1e-7 * max(1.0, length(direction)) for p in points):
        return AtomicLine(points[0], points[-1])
    if closed:
        return interpolate_nurbs_curve(tuple(points), 3, periodic=True)
    return rhino_interpolated_curve(points, CHORD)


def shape_faces(shape) -> list[AtomicSurface]:
    """The faces of a brep, surface or box; anything else raises ``TypeError``."""
    faces = brep_faces(shape)
    if not faces:
        raise TypeError(f"Sections need a brep, surface or box, not {type(shape).__name__}")
    return faces


def brep_plane_section(brep, plane: AtomicPlane, tolerance: float = ABSOLUTE_TOLERANCE) -> list:
    """Section curves of a brep (or surface / box) by a plane: face sections joined end to end. A face
    lying in the plane contributes its boundary, and the neighbouring faces' sections along that
    boundary are dropped (Rhino reports the coplanar face once). Other geometry raises ``TypeError``."""
    faces = shape_faces(brep)
    boundaries: list[AtomicPolyline] = []
    pieces = []
    for face in faces:
        face_plane = _face_is_planar(face)
        if face_plane is not None and all(abs(signed_distance(plane, p)) <= tolerance for row in face.poles for p in row):
            boundaries.extend(surface_plane_section(face, plane, tolerance))
        else:
            pieces.extend(surface_plane_section(face, plane, tolerance))
    if boundaries:
        pieces = [piece for piece in pieces if not _lies_on_polylines(piece, boundaries, tolerance)]
    pieces = boundaries + pieces
    return join_curves(pieces) if len(pieces) > 1 else pieces


def _lies_on_polylines(curve, polylines: Sequence[AtomicPolyline], tolerance: float) -> bool:
    start, end = curve_domain_of(curve)
    for f in (0.0, 0.5, 1.0):
        point = curve_point_at(curve, start + (end - start) * f)
        if not any(_polyline_distance(polyline, point) <= tolerance for polyline in polylines):
            return False
    return True


def _polyline_distance(polyline: AtomicPolyline, point: AtomicPoint) -> float:
    return min(distance(point, _segment_closest(a, b, point)) for a, b in zip(polyline.points, polyline.points[1:]))


def _segment_closest(a: AtomicPoint, b: AtomicPoint, point: AtomicPoint) -> AtomicPoint:
    direction = sub(b, a)
    extent = dot(direction, direction)
    f = 0.0 if extent <= _ZERO else max(0.0, min(1.0, dot(sub(point, a), direction) / extent))
    return AtomicPoint(a.x + direction.x * f, a.y + direction.y * f, a.z + direction.z * f)


def brep_line_intersections(brep, line: AtomicLine, tolerance: float = ABSOLUTE_TOLERANCE) -> tuple[list[AtomicLine], list[AtomicPoint]]:
    """``(overlaps, points)`` for the infinite line and the brep's faces, face by face (Rhino's order):
    stretches lying in planar faces, then the piercing points that are not part of an overlap."""
    overlaps: list[AtomicLine] = []
    points: list[AtomicPoint] = []
    faces = brep_faces(brep)
    for face in faces:
        for overlap in surface_line_overlaps(face, line, tolerance):
            if all(distance(overlap.start, o.start) > 1e-9 or distance(overlap.end, o.end) > 1e-9 for o in overlaps):
                overlaps.append(overlap)
    for face in faces:
        if surface_line_overlaps(face, line, tolerance):
            continue
        for _, _, point, _, _ in surface_line_intersections(face, line):
            if any(_on_segment(point, o, tolerance) for o in overlaps):
                continue
            if all(distance(point, other) > 1e-9 for other in points):
                points.append(point)
    return overlaps, points


def _on_segment(point: AtomicPoint, segment: AtomicLine, tolerance: float) -> bool:
    direction = sub(segment.end, segment.start)
    extent = length(direction)
    if extent <= _ZERO:
        return distance(point, segment.start) <= tolerance
    s = max(0.0, min(extent, dot(sub(point, segment.start), direction) / extent))
    return distance(point, _along(segment.start, unit(direction), s)) <= tolerance


# ── plane regions ──────────────────────────────────────────────────


def plane_region(plane: AtomicPlane, bounds: Sequence[AtomicPlane]) -> AtomicPolyline:
    """Grasshopper's Plane Region: the cell of the plane cut out by the bounding planes around the
    plane's origin (bounds through the origin are ignored, the cell is clipped to a square of 10 units
    or twice the farthest bound); fewer than two effective bounds raise ``ValueError``."""
    lines = []
    for bound in bounds:
        direction = cross(plane.normal, bound.normal)
        if is_zero(direction, 1e-9):
            continue
        # a point on both planes
        d = plane_coordinates(plane, bound.origin)
        n_local = plane_coordinates(AtomicPlane(AtomicPoint(0.0, 0.0, 0.0), plane.normal, plane.x_axis), AtomicPoint(bound.normal.x, bound.normal.y, bound.normal.z))
        nx, ny = n_local[0], n_local[1]
        norm = math.hypot(nx, ny)
        if norm <= 1e-12:
            continue
        nx, ny = nx / norm, ny / norm
        offset = nx * d[0] + ny * d[1]  # line: nx·x + ny·y = offset in plane coordinates
        if abs(offset) <= 1e-9:
            continue  # through the origin: ignored by Grasshopper
        lines.append((nx, ny, offset))
    if len(lines) < 2:
        raise ValueError("At least 3 valid intersections are needed to create a planar region")
    extent = max(10.0, 2.0 * max(abs(offset) for _, _, offset in lines))
    polygon = [(-extent, -extent), (extent, -extent), (extent, extent), (-extent, extent)]
    for nx, ny, offset in lines:
        keep_sign = -1.0 if offset > 0 else 1.0  # the side containing the origin
        polygon = _clip(polygon, lambda x, y, nx=nx, ny=ny, offset=offset, keep_sign=keep_sign: keep_sign * (nx * x + ny * y - offset))
        if len(polygon) < 3:
            raise ValueError("At least 3 valid intersections are needed to create a planar region")
    points = [point_on_plane(plane, x, y) for x, y in polygon]
    return AtomicPolyline(tuple(points + [points[0]]))


def _clip(polygon, inside_value):
    result = []
    count = len(polygon)
    for i in range(count):
        current, following = polygon[i], polygon[(i + 1) % count]
        vc, vf = inside_value(*current), inside_value(*following)
        if vc >= -1e-12:
            result.append(current)
        if (vc >= -1e-12) != (vf >= -1e-12):
            f = vc / (vc - vf)
            result.append((current[0] + (following[0] - current[0]) * f, current[1] + (following[1] - current[1]) * f))
    cleaned = []
    for p in result:
        if not cleaned or math.hypot(p[0] - cleaned[-1][0], p[1] - cleaned[-1][1]) > 1e-9:
            cleaned.append(p)
    if len(cleaned) > 1 and math.hypot(cleaned[0][0] - cleaned[-1][0], cleaned[0][1] - cleaned[-1][1]) <= 1e-9:
        cleaned.pop()
    return cleaned


# ── contours ───────────────────────────────────────────────────────


def contour_offsets(extent: tuple[float, float], start: float, step: float) -> list[float]:
    """Offsets ``start + k·step`` (k integer) with ``min <= offset < max`` in ascending k order."""
    if step <= _ZERO:
        raise ValueError("Contour distance must be greater than zero")
    low, high = extent
    first = math.ceil((low - start) / step - 1e-9)
    offsets = []
    k = first
    while start + k * step < high - 1e-9:
        offsets.append(start + k * step)
        k += 1
    return offsets


def cumulative_offsets(offsets: Sequence[float] | None, distances: Sequence[float] | None) -> list[float]:
    """Grasshopper's Contour (ex) plane offsets: the offsets as given when there are any, else the
    distances accumulated from the first one; neither raises ``ValueError``."""
    if offsets:
        return [float(o) for o in offsets]
    if distances:
        result, total = [], 0.0
        for d in distances:
            total += float(d)
            result.append(total)
        return result
    raise ValueError("You either have to specify Distances or Offsets")


def extent_along(geometry, origin: AtomicPoint, direction: AtomicVector) -> tuple[float, float]:
    """Signed extent of the geometry along *direction* measured from *origin*, hugging the geometry
    (dense sampling for NURBS) like Rhino's accurate bounding box."""
    from pyhopper.Utils.Bounds import tight_extents
    from pyhopper.Utils.Planes import plane_from_normal

    extents = tight_extents(geometry, plane_from_normal(origin, direction))
    if extents is None:
        raise ValueError("Cannot contour empty geometry")
    return extents[2]


def offset_plane(plane: AtomicPlane, offset: float) -> AtomicPlane:
    n = unit(plane.normal)
    return AtomicPlane(AtomicPoint(plane.origin.x + n.x * offset, plane.origin.y + n.y * offset, plane.origin.z + n.z * offset), plane.normal, plane.x_axis)


# ── region trimming ────────────────────────────────────────────────


def trim_with_regions(curve, regions: Sequence, plane: AtomicPlane | None, tolerance: float = ABSOLUTE_TOLERANCE) -> tuple[list, list]:
    """Grasshopper's Trim with Region(s): the curve split where its projection crosses the region
    boundaries (in the given plane, or the first region's plane; a stretch running along a boundary is
    cut only where it starts, like Grasshopper); every piece goes to *inside* when its midpoint projects
    inside or onto any region (Grasshopper counts a coincident midpoint as inside), else to *outside*.
    Open regions raise ``ValueError``."""
    from pyhopper.Utils.ClosestPoints import point_in_closed_curve

    regions = list(regions)
    if not regions:
        raise ValueError("Trim needs at least one region")
    for region in regions:
        if not curve_is_closed(region):
            raise ValueError("Curves should only be trimmed with a closed Region.")
    reference = plane
    if reference is None:
        first = regions[0]
        reference = first.plane if isinstance(first, (AtomicArc, AtomicCircle, AtomicRectangle)) else curve_planarity(first)[0]

    def mapper(point: AtomicPoint) -> AtomicPoint:
        return project_point(reference, point)

    cuts: list[float] = []
    for region in regions:
        for ta, _, _ in curve_curve_intersections(curve, region, tolerance, reference, overlap_ends=False):
            cuts.append(ta)
    start, end = curve_domain_of(curve)
    pieces = shatter(curve, cuts) if cuts else [curve]
    if not cuts:
        pieces = [curve]
    inside, outside = [], []
    for piece in pieces:
        p0, p1 = curve_domain_of(piece)
        middle = mapper(curve_point_at(piece, 0.5 * (p0 + p1)))
        contained = False
        for region in regions:
            try:
                relationship, _ = point_in_closed_curve(region, middle, tolerance)
            except ValueError:
                continue
            if relationship in (1, 2):
                contained = True
                break
        (inside if contained else outside).append(piece)
    return inside, outside
