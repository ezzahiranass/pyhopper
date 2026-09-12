"""Closed-form tangency constructions for the Curve > Primitive components.

Tangent lines between points and circles, circles tangent to lines and circles
(the two- and three-curve Apollonius problems), fillet arcs between circles,
biarcs and the Steiner inellipse — all with the conventions read off
Grasshopper 8 (which tangent is "the first", where arcs start, how the second
biarc arc is oriented).
"""

from __future__ import annotations

import math
from typing import Sequence

from pyhopper.Core.Atoms import AtomicArc, AtomicCircle, AtomicInterval, AtomicLine, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Utils.Planes import plane_coordinates, plane_from_points, point_on_plane
from pyhopper.Utils.Vectors import cross, distance, dot, is_zero, sub, unit

_TOLERANCE = 1e-9


# ── planes and 2D helpers ──────────────────────────────────────────

def working_plane(items: Sequence) -> AtomicPlane:
    """The plane shared by circles, arcs and lines (the first circle's plane, or the plane through
    the lines' points); everything is measured in its coordinates."""
    for item in items:
        if isinstance(item, (AtomicCircle, AtomicArc)):
            return item.plane
    points = []
    for item in items:
        if isinstance(item, AtomicLine):
            points.extend((item.start, item.end))
        elif isinstance(item, AtomicPoint):
            points.append(item)
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            for k in range(j + 1, len(points)):
                try:
                    return plane_from_points(points[i], points[j], points[k])
                except ValueError:
                    continue
    return AtomicPlane.world_xy(points[0] if points else None)


def _xy(plane: AtomicPlane, point: AtomicPoint) -> tuple[float, float]:
    x, y, _ = plane_coordinates(plane, point)
    return x, y


def _point(plane: AtomicPlane, x: float, y: float) -> AtomicPoint:
    return point_on_plane(plane, x, y)


class _Line2D:
    """A 2D line ``origin + t·direction`` with unit direction."""

    def __init__(self, ox: float, oy: float, dx: float, dy: float):
        length = math.hypot(dx, dy)
        if length <= _TOLERANCE:
            raise ValueError("Degenerate line")
        self.ox, self.oy, self.dx, self.dy = ox, oy, dx / length, dy / length
        self.nx, self.ny = -self.dy, self.dx  # left normal

    def signed_distance(self, x: float, y: float) -> float:
        return (x - self.ox) * self.nx + (y - self.oy) * self.ny

    def closest(self, x: float, y: float) -> tuple[float, float]:
        t = (x - self.ox) * self.dx + (y - self.oy) * self.dy
        return self.ox + t * self.dx, self.oy + t * self.dy


class _Circle2D:
    def __init__(self, cx: float, cy: float, radius: float):
        self.cx, self.cy, self.radius = cx, cy, float(radius)

    def closest(self, x: float, y: float) -> tuple[float, float]:
        dx, dy = x - self.cx, y - self.cy
        length = math.hypot(dx, dy)
        if length <= _TOLERANCE:
            return self.cx + self.radius, self.cy
        return self.cx + dx / length * self.radius, self.cy + dy / length * self.radius


def _flatten(plane: AtomicPlane, curve):
    if isinstance(curve, AtomicLine):
        sx, sy = _xy(plane, curve.start)
        ex, ey = _xy(plane, curve.end)
        return _Line2D(sx, sy, ex - sx, ey - sy)
    if isinstance(curve, (AtomicCircle, AtomicArc)):
        cx, cy = _xy(plane, curve.plane.origin)
        return _Circle2D(cx, cy, curve.radius)
    raise TypeError(f"Tangency constructions accept lines, circles and arcs, not {type(curve).__name__} (curve closest points arrive with the K3 kernel)")


def _circle(plane: AtomicPlane, cx: float, cy: float, radius: float) -> AtomicCircle:
    centre = _point(plane, cx, cy)
    return AtomicCircle(AtomicPlane(centre, plane.normal, plane.x_axis), radius)


# ── tangent lines ──────────────────────────────────────────────────

def tangent_lines_point_circle(point: AtomicPoint, circle: AtomicCircle) -> tuple[AtomicLine, AtomicLine]:
    """The two tangents from ``point`` to ``circle`` (Grasshopper's Tangent Lines): the first meets
    the circle counter-clockwise of the direction centre → point, the second clockwise."""
    plane = circle.plane
    px, py = _xy(plane, point)
    cx, cy = _xy(plane, circle.plane.origin)
    dx, dy = px - cx, py - cy
    d = math.hypot(dx, dy)
    if d <= circle.radius + _TOLERANCE:
        raise ValueError("Tangent Lines: the circle contains the point, no tangents are possible")
    base = math.atan2(dy, dx)
    theta = math.acos(circle.radius / d)
    lines = []
    for sign in (1.0, -1.0):
        angle = base + sign * theta
        tangent = _point(plane, cx + circle.radius * math.cos(angle), cy + circle.radius * math.sin(angle))
        lines.append(AtomicLine(point, tangent))
    return lines[0], lines[1]


def _circle_pair(circle_a: AtomicCircle, circle_b: AtomicCircle):
    plane = circle_a.plane
    ax, ay = _xy(plane, circle_a.plane.origin)
    bx, by = _xy(plane, circle_b.plane.origin)
    return plane, ax, ay, bx, by, math.hypot(bx - ax, by - ay), math.atan2(by - ay, bx - ax)


def external_tangent_lines(circle_a: AtomicCircle, circle_b: AtomicCircle) -> tuple[AtomicLine, AtomicLine]:
    """External tangents from circle A to circle B (first counter-clockwise of the A → B direction)."""
    plane, ax, ay, bx, by, d, base = _circle_pair(circle_a, circle_b)
    ra, rb = float(circle_a.radius), float(circle_b.radius)
    if d <= abs(ra - rb) + _TOLERANCE:
        raise ValueError("Tangent Lines (Ex): one circle contains the other, no external tangents are possible")
    theta = math.acos((ra - rb) / d)
    lines = []
    for sign in (1.0, -1.0):
        angle = base + sign * theta
        lines.append(AtomicLine(_point(plane, ax + ra * math.cos(angle), ay + ra * math.sin(angle)), _point(plane, bx + rb * math.cos(angle), by + rb * math.sin(angle))))
    return lines[0], lines[1]


def internal_tangent_lines(circle_a: AtomicCircle, circle_b: AtomicCircle) -> tuple[AtomicLine, AtomicLine]:
    """Internal (crossing) tangents from circle A to circle B (first leaves A counter-clockwise)."""
    plane, ax, ay, bx, by, d, base = _circle_pair(circle_a, circle_b)
    ra, rb = float(circle_a.radius), float(circle_b.radius)
    if d <= ra + rb + _TOLERANCE:
        raise ValueError("Tangent Lines (In): the circles intersect, no internal tangents are possible")
    theta = math.acos((ra + rb) / d)
    lines = []
    for sign in (1.0, -1.0):
        angle = base + sign * theta
        lines.append(AtomicLine(_point(plane, ax + ra * math.cos(angle), ay + ra * math.sin(angle)), _point(plane, bx - rb * math.cos(angle), by - rb * math.sin(angle))))
    return lines[0], lines[1]


# ── tangent circles ────────────────────────────────────────────────

def tangent_circle_two(curve_a, curve_b, point: AtomicPoint) -> AtomicCircle:
    """Circle tangent to curve B at B's point closest to ``point``, and tangent to curve A, lying on
    the point's side of B (Grasshopper's Circle TanTan, verified for lines and circles)."""
    plane = working_plane([curve_a, curve_b])
    shape_a, shape_b = _flatten(plane, curve_a), _flatten(plane, curve_b)
    px, py = _xy(plane, point)
    qx, qy = shape_b.closest(px, py)
    # unit normal of B at Q pointing towards the point (its side)
    if isinstance(shape_b, _Line2D):
        side = shape_b.signed_distance(px, py)
        sign = 1.0 if side >= 0.0 else -1.0
        nx, ny = shape_b.nx * sign, shape_b.ny * sign
    else:
        rx, ry = qx - shape_b.cx, qy - shape_b.cy
        length = math.hypot(rx, ry)
        nx, ny = rx / length, ry / length
        if math.hypot(px - shape_b.cx, py - shape_b.cy) < shape_b.radius:
            nx, ny = -nx, -ny
    # centre = Q + s·n with radius s; tangency to A fixes s
    candidates = []
    if isinstance(shape_a, _Line2D):
        w = shape_a.signed_distance(qx, qy)
        m = nx * shape_a.nx + ny * shape_a.ny
        for sign in (1.0, -1.0):
            denominator = sign - m
            if abs(denominator) > _TOLERANCE:
                candidates.append(w / denominator)
    else:
        ux, uy = qx - shape_a.cx, qy - shape_a.cy
        base = ux * ux + uy * uy - shape_a.radius ** 2
        for sign in (1.0, -1.0):  # external first, then internal tangency with A
            denominator = 2.0 * (sign * shape_a.radius - (nx * ux + ny * uy))
            if abs(denominator) > _TOLERANCE:
                candidates.append(base / denominator)
    radii = [s for s in candidates if s > _TOLERANCE]
    if not radii:
        raise ValueError("Circle TanTan: no circle is tangent to both curves near the point")
    s = radii[0]
    return _circle(plane, qx + s * nx, qy + s * ny, s)


def tangent_circle_three(curves: Sequence, point: AtomicPoint) -> AtomicCircle:
    """The Apollonius circle tangent to three lines/circles whose centre is closest to ``point``."""
    plane = working_plane(list(curves))
    shapes = [_flatten(plane, curve) for curve in curves]
    px, py = _xy(plane, point)
    solutions = []
    for signs in ((a, b, c) for a in (1.0, -1.0) for b in (1.0, -1.0) for c in (1.0, -1.0)):
        solution = _apollonius_newton(shapes, signs, px, py)
        if solution is not None and all(abs(solution[0] - other[0]) > 1e-7 or abs(solution[1] - other[1]) > 1e-7 or abs(solution[2] - other[2]) > 1e-7 for other in solutions):
            solutions.append(solution)
    if not solutions:
        raise ValueError("Circle TanTanTan: no circle is tangent to all three curves")
    cx, cy, r = min(solutions, key=lambda s: math.hypot(s[0] - px, s[1] - py))
    return _circle(plane, cx, cy, r)


def _apollonius_newton(shapes, signs, px: float, py: float):
    """Newton iteration on (centre, radius) for one choice of tangency sides; None when it fails."""
    # residuals: circle -> |c - ci| - (r + sign*ri) = 0 ; line -> sign*signed_distance - r = 0
    cx, cy = px, py
    r = sum(_residual_distance(shape, px, py) for shape in shapes) / len(shapes) or 1.0
    for _ in range(60):
        f, jac = [], []
        for shape, sign in zip(shapes, signs):
            if isinstance(shape, _Circle2D):
                dx, dy = cx - shape.cx, cy - shape.cy
                dist = math.hypot(dx, dy)
                if dist <= _TOLERANCE:
                    return None
                f.append(dist - (r + sign * shape.radius))
                jac.append([dx / dist, dy / dist, -1.0])
            else:
                f.append(sign * shape.signed_distance(cx, cy) - r)
                jac.append([sign * shape.nx, sign * shape.ny, -1.0])
        step = _solve3(jac, [-v for v in f])
        if step is None:
            return None
        cx, cy, r = cx + step[0], cy + step[1], r + step[2]
        if max(abs(v) for v in step) < 1e-13:
            break
    if r <= 1e-9 or any(abs(v) > 1e-7 for v in f) or not all(math.isfinite(v) for v in (cx, cy, r)):
        return None
    return cx, cy, r


def _residual_distance(shape, x: float, y: float) -> float:
    if isinstance(shape, _Circle2D):
        return abs(math.hypot(x - shape.cx, y - shape.cy) - shape.radius)
    return abs(shape.signed_distance(x, y))


def _solve3(matrix, rhs):
    m = [row[:] + [value] for row, value in zip(matrix, rhs)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda row: abs(m[row][col]))
        if abs(m[pivot][col]) <= 1e-14:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        for row in range(3):
            if row != col:
                factor = m[row][col] / m[col][col]
                m[row] = [a - factor * b for a, b in zip(m[row], m[col])]
    return [m[i][3] / m[i][i] for i in range(3)]


# ── tangent arcs between circles ───────────────────────────────────

def tangent_arcs(circle_a: AtomicCircle, circle_b: AtomicCircle, radius: float) -> tuple[AtomicArc, AtomicArc]:
    """The two fillet arcs of ``radius`` externally tangent to both circles, each running from its
    tangent point on A to its tangent point on B through the gap between the circles; arc A has its
    centre on the right of the A → B direction (Grasshopper-verified)."""
    plane, ax, ay, bx, by, d, _ = _circle_pair(circle_a, circle_b)
    ra, rb, r = float(circle_a.radius), float(circle_b.radius), float(radius)
    if r <= 0.0:
        raise ValueError("Tangent Arcs needs a positive radius")
    la, lb = ra + r, rb + r
    if d <= _TOLERANCE or d > la + lb + _TOLERANCE or d < abs(la - lb) - _TOLERANCE:
        raise ValueError("Tangent Arcs: the gap between the circles does not fit the fillet radius")
    # centres at the intersections of the circles (A, ra + r) and (B, rb + r)
    along = (la * la - lb * lb + d * d) / (2.0 * d)
    height = math.sqrt(max(la * la - along * along, 0.0))
    ux, uy = (bx - ax) / d, (by - ay) / d
    mx, my = ax + along * ux, ay + along * uy
    arcs = {}
    for side, label in ((-1.0, "a"), (1.0, "b")):  # right of A -> B first
        cx, cy = mx + side * height * (-uy), my + side * height * ux
        arcs[label] = _fillet_arc(plane, cx, cy, r, ax, ay, bx, by)
    return arcs["a"], arcs["b"]


def _fillet_arc(plane: AtomicPlane, cx: float, cy: float, r: float, ax: float, ay: float, bx: float, by: float) -> AtomicArc:
    """Arc of the circle (c, r) from its tangent point with A to its tangent point with B, sweeping
    through the side that faces the two circles."""
    start = math.atan2(ay - cy, ax - cx)
    end = math.atan2(by - cy, bx - cx)
    sweep = (end - start) % (2.0 * math.pi)
    # the arc must pass between the circles: pick the orientation whose midpoint faces their midpoint
    gap_x, gap_y = (ax + bx) / 2.0, (ay + by) / 2.0
    mid_ccw = (cx + r * math.cos(start + sweep / 2.0), cy + r * math.sin(start + sweep / 2.0))
    mid_cw = (cx + r * math.cos(start - (2.0 * math.pi - sweep) / 2.0), cy + r * math.sin(start - (2.0 * math.pi - sweep) / 2.0))
    centre = _point(plane, cx, cy)
    x_axis = unit(sub(_point(plane, cx + math.cos(start), cy + math.sin(start)), centre))
    if math.hypot(mid_ccw[0] - gap_x, mid_ccw[1] - gap_y) <= math.hypot(mid_cw[0] - gap_x, mid_cw[1] - gap_y):
        return AtomicArc(AtomicPlane(centre, plane.normal, x_axis), r, AtomicInterval(0.0, sweep))
    flipped = AtomicVector(-plane.normal.x, -plane.normal.y, -plane.normal.z)
    return AtomicArc(AtomicPlane(centre, flipped, x_axis), r, AtomicInterval(0.0, 2.0 * math.pi - sweep))


# ── biarc ──────────────────────────────────────────────────────────

def biarc(start: AtomicPoint, start_tangent: AtomicVector, end: AtomicPoint, end_tangent: AtomicVector, ratio: float) -> tuple[AtomicArc, AtomicArc, AtomicNurbsCurve]:
    """Biarc from ``start`` to ``end`` with the given (unitised) tangents. The tangent lengths of the
    two arcs are split ``ratio : 1 - ratio`` (0.5 gives the equal-tangent biarc, which is what
    Grasshopper draws at its default). Returns both arcs (the second stored Rhino's way: x axis at the
    end point, negative start angle) and the joined rational NURBS curve — or the single arc when both
    arcs lie on one circle.
    """
    rho = float(ratio)
    if not 0.0 < rho < 1.0:
        raise ValueError("BiArc ratio must lie strictly between 0 and 1")
    t0, t1 = unit(start_tangent), unit(end_tangent)
    if is_zero(t0) or is_zero(t1):
        raise ValueError("BiArc needs non-zero tangents")
    chord = sub(end, start)
    c2, ct0, ct1, t0t1 = dot(chord, chord), dot(chord, t0), dot(chord, t1), dot(t0, t1)
    if c2 <= _TOLERANCE:
        raise ValueError("BiArc needs distinct end points")
    # tangent lengths a = k·rho, b = k·(1 - rho) with |V2 - V1| = a + b
    p, q = rho, 1.0 - rho
    quad_a = 2.0 * p * q * (t0t1 - 1.0)
    quad_b = -2.0 * (p * ct0 + q * ct1)
    k = _positive_root(quad_a, quad_b, c2)
    if k is None:
        raise ValueError("BiArc could not be fitted to these end conditions")
    a, b = k * p, k * q
    v1 = AtomicPoint(start.x + a * t0.x, start.y + a * t0.y, start.z + a * t0.z)
    v2 = AtomicPoint(end.x - b * t1.x, end.y - b * t1.y, end.z - b * t1.z)
    joint_direction = unit(sub(v2, v1))
    joint = AtomicPoint(v1.x + a * joint_direction.x, v1.y + a * joint_direction.y, v1.z + a * joint_direction.z)
    arc_a = _arc_from_tangent(start, t0, joint, reverse=False)
    arc_b = _arc_from_tangent(end, AtomicVector(-t1.x, -t1.y, -t1.z), joint, reverse=True)
    if distance(arc_a.plane.origin, arc_b.plane.origin) <= 1e-9 * max(1.0, arc_a.radius) and abs(arc_a.radius - arc_b.radius) <= 1e-9 * max(1.0, arc_a.radius):
        # co-circular biarc: Rhino continues the first arc's frame and returns one arc for the whole
        total = float(arc_a.angle.end) + abs(float(arc_b.angle.start))
        arc_b = AtomicArc(arc_a.plane, arc_a.radius, AtomicInterval(float(arc_a.angle.end), total))
        return arc_a, arc_b, AtomicArc(arc_a.plane, arc_a.radius, AtomicInterval(0.0, total))
    return arc_a, arc_b, _join_arcs(arc_a, arc_b)


def _positive_root(a: float, b: float, c: float):
    if abs(a) <= 1e-14:
        if abs(b) <= 1e-14:
            return None
        root = -c / b
        return root if root > _TOLERANCE else None
    discriminant = b * b - 4.0 * a * c
    if discriminant < 0.0:
        return None
    roots = [(-b - math.sqrt(discriminant)) / (2.0 * a), (-b + math.sqrt(discriminant)) / (2.0 * a)]
    positive = [root for root in roots if root > _TOLERANCE]
    return min(positive) if positive else None


def _arc_from_tangent(anchor: AtomicPoint, tangent: AtomicVector, target: AtomicPoint, *, reverse: bool) -> AtomicArc:
    """Arc leaving ``anchor`` along ``tangent`` and reaching ``target``. With ``reverse`` the arc is
    stored the way Rhino stores the second biarc arc: x axis at the anchor and a negative start angle,
    so that its parameter runs from the target to the anchor."""
    chord = sub(target, anchor)
    length2 = dot(chord, chord)
    normal = cross(tangent, chord)
    if is_zero(normal, 1e-9) or length2 <= _TOLERANCE:
        raise ValueError("BiArc could not be fitted: one arc is a straight line")
    normal = unit(normal)
    # centre = anchor + r·(normal × tangent): |centre - target| = r  ->  r = |chord|² / (2 chord·(n × t))
    inward = cross(normal, tangent)
    r = length2 / (2.0 * dot(chord, inward))
    centre = AtomicPoint(anchor.x + r * inward.x, anchor.y + r * inward.y, anchor.z + r * inward.z)
    x_axis = unit(sub(anchor, centre))
    y_axis = cross(normal, x_axis)
    to_target = sub(target, centre)
    sweep = math.atan2(dot(to_target, y_axis), dot(to_target, x_axis)) % (2.0 * math.pi)
    if reverse:
        # flip the normal so the target sits at the negative angle and the parameter runs target -> anchor
        flipped = AtomicVector(-normal.x, -normal.y, -normal.z)
        return AtomicArc(AtomicPlane(centre, flipped, x_axis), r, AtomicInterval(-sweep, 0.0))
    return AtomicArc(AtomicPlane(centre, normal, x_axis), r, AtomicInterval(0.0, sweep))


def arc_nurbs_rhino(arc: AtomicArc) -> AtomicNurbsCurve:
    """Rhino's rational quadratic NURBS form of an arc: one span per quarter turn, knots in arc length."""
    from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

    nurbs = as_nurbs_curve(arc)
    length = abs(float(arc.angle.end) - float(arc.angle.start)) * float(arc.radius)
    return AtomicNurbsCurve(nurbs.control_points, nurbs.weights, tuple(k * length for k in nurbs.knots), nurbs.degree)


def _join_arcs(arc_a: AtomicArc, arc_b: AtomicArc) -> AtomicNurbsCurve:
    first, second = arc_nurbs_rhino(arc_a), arc_nurbs_rhino(arc_b)
    offset = first.knots[-1]
    # a C0 join of two quadratics carries a double knot: drop one end knot and the second's start triple
    knots = tuple(first.knots[:-1]) + tuple(offset + k for k in second.knots[3:])
    return AtomicNurbsCurve(first.control_points + second.control_points[1:], first.weights + second.weights[1:], knots, 2)


# ── Steiner inellipse ──────────────────────────────────────────────

def steiner_inellipse(a: AtomicPoint, b: AtomicPoint, c: AtomicPoint) -> tuple[AtomicNurbsCurve, AtomicPlane]:
    """Grasshopper's InEllipse: the incircle of the unit equilateral triangle mapped affinely onto the
    triangle ABC (a rational quadratic NURBS with Rhino's circle knots), plus the plane through the
    corners (origin A, x axis towards B)."""
    plane = plane_from_points(a, b, c)
    from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

    radius = 1.0 / (2.0 * math.sqrt(3.0))
    circle = as_nurbs_curve(AtomicCircle(AtomicPlane.world_xy(AtomicPoint(0.5, radius, 0.0)), radius))
    # affine map: (1, 0) -> B - A, (0.5, sqrt(3)/2) -> C - A
    e1 = sub(b, a)
    ca = sub(c, a)
    root3 = math.sqrt(3.0) / 2.0
    e2 = AtomicVector((ca.x - 0.5 * e1.x) / root3, (ca.y - 0.5 * e1.y) / root3, (ca.z - 0.5 * e1.z) / root3)
    points = tuple(AtomicPoint(a.x + p.x * e1.x + p.y * e2.x, a.y + p.x * e1.y + p.y * e2.y, a.z + p.x * e1.z + p.y * e2.z) for p in circle.control_points)
    length = 2.0 * math.pi * radius
    return AtomicNurbsCurve(points, circle.weights, tuple(k * length for k in circle.knots), 2), plane
