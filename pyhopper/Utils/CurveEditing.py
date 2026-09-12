"""Polyline and control-polygon editing for the Curve > Util components.

Grasshopper-verified rules: Polyline Collapse merges the shortest short segment
first, Smooth Polyline pulls each vertex half-way (times ``strength``) towards
its neighbours' midpoint, Reduce is Douglas-Peucker, Simplify merges polyline
segments that turn by no more than the angle tolerance and turns straight
NURBS into lines, and the loose offset moves the control polygon's vertices to
the intersections of its offset edges.
"""

from __future__ import annotations

import math
from typing import Sequence

from pyhopper.Core.Atoms import AtomicArc, AtomicCircle, AtomicLine, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicPolyline, AtomicVector
from pyhopper.Utils.Vectors import angle, cross, distance, dot, is_zero, scale, sub, unit

_TOLERANCE = 1e-12


def polyline_points(curve) -> list[AtomicPoint]:
    """The vertices of a polyline-like curve (polylines, lines, degree-1 NURBS)."""
    if isinstance(curve, AtomicPolyline):
        return list(curve.points)
    if isinstance(curve, AtomicLine):
        return [curve.start, curve.end]
    if isinstance(curve, AtomicNurbsCurve) and curve.degree == 1:
        return list(curve.control_points)
    raise TypeError(f"expected a polyline, not {type(curve).__name__}")


def _midpoint(a: AtomicPoint, b: AtomicPoint) -> AtomicPoint:
    return AtomicPoint((a.x + b.x) / 2.0, (a.y + b.y) / 2.0, (a.z + b.z) / 2.0)


def collapse_short_segments(points: Sequence[AtomicPoint], tolerance: float) -> tuple[list[AtomicPoint], int]:
    """Repeatedly collapse the shortest segment while it is shorter than ``tolerance`` (ties go to the
    first): interior pairs merge into their midpoint, a segment touching an end keeps the end point;
    a polyline never drops below two points. Returns the points and the number of collapses."""
    pts = list(points)
    count = 0
    while len(pts) > 2:
        lengths = [distance(a, b) for a, b in zip(pts, pts[1:])]
        index = min(range(len(lengths)), key=lambda i: (lengths[i], i))
        if lengths[index] >= float(tolerance):
            break
        if index == 0:
            del pts[1]
        elif index == len(lengths) - 1:
            del pts[index]
        else:
            pts[index:index + 2] = [_midpoint(pts[index], pts[index + 1])]
        count += 1
    return pts, count


def smooth_polyline(points: Sequence[AtomicPoint], strength: float, times: int) -> list[AtomicPoint]:
    """Each pass moves every vertex ``strength / 2`` of the way towards the midpoint of its neighbours
    (simultaneously); the ends of an open polyline stay, a closed polyline wraps around."""
    pts = list(points)
    rounds = int(times)
    if rounds < 0:
        raise ValueError("smoothing needs a non-negative number of passes")
    if len(pts) < 3:
        return pts
    closed = distance(pts[0], pts[-1]) <= 1e-9
    factor = float(strength) / 2.0
    for _ in range(rounds):
        core = pts[:-1] if closed else pts
        n = len(core)
        smoothed = []
        for i, p in enumerate(core):
            if not closed and i in (0, n - 1):
                smoothed.append(p)
                continue
            a, b = core[(i - 1) % n], core[(i + 1) % n]
            smoothed.append(AtomicPoint(p.x + factor * ((a.x + b.x) / 2.0 - p.x), p.y + factor * ((a.y + b.y) / 2.0 - p.y), p.z + factor * ((a.z + b.z) / 2.0 - p.z)))
        pts = smoothed + [smoothed[0]] if closed else smoothed
    return pts


def _segment_distance(point: AtomicPoint, start: AtomicPoint, end: AtomicPoint) -> float:
    direction = sub(end, start)
    span = dot(direction, direction)
    if span <= _TOLERANCE:
        return distance(point, start)
    t = min(max(dot(sub(point, start), direction) / span, 0.0), 1.0)
    return distance(point, AtomicPoint(start.x + t * direction.x, start.y + t * direction.y, start.z + t * direction.z))


def reduce_polyline(points: Sequence[AtomicPoint], tolerance: float) -> tuple[list[AtomicPoint], int]:
    """Douglas-Peucker reduction: vertices closer than ``tolerance`` to the chord of their run are
    dropped, the farthest one of each run is kept. Returns the points and the number removed."""
    pts = list(points)
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True

    def refine(lo: int, hi: int) -> None:
        if hi - lo < 2:
            return
        farthest, best = -1, -1.0
        for i in range(lo + 1, hi):
            d = _segment_distance(pts[i], pts[lo], pts[hi])
            if d > best:
                farthest, best = i, d
        if best > float(tolerance):
            keep[farthest] = True
            refine(lo, farthest)
            refine(farthest, hi)

    refine(0, len(pts) - 1)
    reduced = [p for p, k in zip(pts, keep) if k]
    return reduced, len(pts) - len(reduced)


def simplify_polyline(points: Sequence[AtomicPoint], tolerance: float, angle_tolerance: float) -> list[AtomicPoint]:
    """Drop vertices where the polyline turns by no more than ``angle_tolerance`` and deviates from the
    merged segment by no more than ``tolerance``."""
    pts = list(points)
    changed = True
    while changed and len(pts) > 2:
        changed = False
        for i in range(1, len(pts) - 1):
            turn = angle(sub(pts[i], pts[i - 1]), sub(pts[i + 1], pts[i]))
            if turn <= float(angle_tolerance) + 1e-12 and _segment_distance(pts[i], pts[i - 1], pts[i + 1]) <= float(tolerance) + 1e-12:
                del pts[i]
                changed = True
                break
    return pts


def collinear_points(points: Sequence[AtomicPoint], tolerance: float) -> bool:
    pts = list(points)
    if len(pts) < 3:
        return True
    return all(_segment_distance(p, pts[0], pts[-1]) <= tolerance for p in pts[1:-1])


def simplify_curve(curve, tolerance: float, angle_tolerance: float):
    """Grasshopper's Simplify Curve: polylines lose collinear vertices (a single segment becomes a
    line), NURBS with collinear control points become lines and other NURBS are reported simplified
    but left alone (Rhino's quirk); lines, circles and arcs are already simple."""
    if isinstance(curve, (AtomicLine, AtomicCircle, AtomicArc)):
        return curve, False
    if isinstance(curve, AtomicPolyline):
        pts = simplify_polyline(curve.points, tolerance, angle_tolerance)
        if len(pts) == 2:
            return AtomicLine(pts[0], pts[1]), True
        return AtomicPolyline(tuple(pts)), len(pts) != len(curve.points)
    if isinstance(curve, AtomicNurbsCurve):
        if collinear_points(curve.control_points, tolerance):
            return AtomicLine(curve.control_points[0], curve.control_points[-1]), True
        return curve, True
    return curve, False


def offset_control_polygon(curve: AtomicNurbsCurve, distance_along: float, plane: AtomicPlane) -> AtomicNurbsCurve:
    """Move every control point to where the offset edges of the control polygon meet: end points move
    ``distance`` along ``edge × normal``, interior points along the bisector of their two edges
    crossed with the normal, by ``distance / cos(half the turning angle)`` (Grasshopper-verified)."""
    pts = list(curve.control_points)
    if len(pts) < 2:
        raise ValueError("a curve needs at least two control points")
    normal = unit(plane.normal)
    d = float(distance_along)
    closed = distance(pts[0], pts[-1]) <= 1e-9 and len(pts) > 2
    moved = []
    for i, p in enumerate(pts):
        if closed and i in (0, len(pts) - 1):
            previous, following = pts[-2], pts[1]
        elif i == 0:
            previous, following = None, pts[1]
        elif i == len(pts) - 1:
            previous, following = pts[-2], None
        else:
            previous, following = pts[i - 1], pts[i + 1]
        incoming = unit(sub(p, previous)) if previous is not None else None
        outgoing = unit(sub(following, p)) if following is not None else None
        if incoming is None or outgoing is None:
            edge = incoming if incoming is not None else outgoing
            direction = cross(edge, normal)
            length = d
        else:
            bisector = AtomicVector(incoming.x + outgoing.x, incoming.y + outgoing.y, incoming.z + outgoing.z)
            direction = cross(bisector, normal)
            half = angle(incoming, outgoing) / 2.0
            length = d / math.cos(half) if math.cos(half) > 1e-9 else d
        if is_zero(direction, 1e-12):
            moved.append(p)
            continue
        step = scale(unit(direction), length)
        moved.append(AtomicPoint(p.x + step.x, p.y + step.y, p.z + step.z))
    return AtomicNurbsCurve(tuple(moved), curve.weights, curve.knots, curve.degree)


def polyline_as_bezier_spans(points: Sequence[AtomicPoint], degree: int) -> AtomicNurbsCurve:
    """The polyline as an exact degree-``degree`` NURBS: one Bezier span per segment with the control
    points spread evenly along it and knots at the cumulative chord lengths (Rhino's Fit of a polyline)."""
    pts = list(points)
    deg = int(degree)
    controls: list[AtomicPoint] = [pts[0]]
    knots: list[float] = [0.0] * (deg + 1)
    offset = 0.0
    for a, b in zip(pts, pts[1:]):
        for k in range(1, deg + 1):
            t = k / deg
            controls.append(AtomicPoint(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t))
        offset += distance(a, b)
        knots.extend([offset] * deg)
    knots.append(offset)
    return AtomicNurbsCurve(tuple(controls), tuple(1.0 for _ in controls), tuple(knots), deg)


def rhino_knot_vector(count: int, degree: int, periodic: bool) -> list[float]:
    """Grasshopper's Knot Vector: Rhino-style (no superfluous end knots) integer knots — clamped
    ``[0]*d, 1, 2 …, [n-d]*d`` or the uniform run ``0 … n+d-2`` for periodic curves. A degree above
    ``count - 1`` is clamped to it (Grasshopper warns)."""
    n, d = int(count), int(degree)
    if n < 2:
        raise ValueError("Knot Vector needs at least two control points")
    if d < 1:
        raise ValueError("Knot Vector needs a degree of at least one")
    d = min(d, n - 1)
    if periodic:
        return [float(i) for i in range(n + d - 1)]
    return [0.0] * d + [float(i) for i in range(1, n - d)] + [float(n - d)] * d


def fit_nurbs_curve(curve: AtomicNurbsCurve, degree: int, tolerance: float, samples: int = 64) -> AtomicNurbsCurve:
    """Least-squares refit of ``curve`` with the fewest control points whose sampled deviation (at
    matching normalised parameters) stays within ``tolerance``; falls back to the source point count."""
    from pyhopper.Utils.CurveFitting import rebuild_curve
    from pyhopper.Utils.Curves import curve_domain_of, curve_point_at

    p = max(1, int(degree))
    start, end = curve_domain_of(curve)
    targets = [curve_point_at(curve, start + (end - start) * i / samples) for i in range(samples + 1)]
    limit = max(len(curve.control_points), p + 1)
    best = None
    for count in range(p + 1, limit + 1):
        rebuilt = rebuild_curve(curve, count, p)
        r_start, r_end = curve_domain_of(rebuilt)
        deviation = max(distance(target, curve_point_at(rebuilt, r_start + (r_end - r_start) * i / samples)) for i, target in enumerate(targets))
        best = rebuilt
        if deviation <= float(tolerance):
            return rebuilt
    return best
