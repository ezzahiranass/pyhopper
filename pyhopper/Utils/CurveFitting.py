"""Curve construction that fits or converts geometry: least-squares lines, circles and
NURBS rebuilds, catenaries, polyline approximations and curve reversal.

Everything is pure Python; the NURBS pieces build on :mod:`pyhopper.Utils.Nurbs`.
"""

from __future__ import annotations

import math
from typing import Sequence

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicInterval,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicRectangle,
    AtomicVector,
)
from pyhopper.Utils.Curves import curve_domain_of, curve_point_at, curve_tangent_at
from pyhopper.Utils.Fitting import fit_plane, jacobi_eigen_symmetric
from pyhopper.Utils.Nurbs import basis_functions, find_span, solve_linear_system
from pyhopper.Utils.Planes import plane_xy, point_on_plane
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Utils.Vectors import cross, distance, dot, is_zero, length, scale, sub, unit


# ── lines and circles ──────────────────────────────────────────────


def _centroid(points: Sequence[AtomicPoint]) -> AtomicPoint:
    count = len(points)
    return AtomicPoint(sum(p.x for p in points) / count, sum(p.y for p in points) / count, sum(p.z for p in points) / count)


def fit_line(points: Sequence[AtomicPoint]) -> AtomicLine:
    """Least-squares line through ``points``, spanning their extent along the fitted direction.

    The direction is the principal axis of the point cloud, oriented so that its
    largest component is positive (Rhino's fit picks the same sign for the usual
    cases); the ends are the extreme projections of the points onto that axis.
    """
    if len(points) < 2:
        raise ValueError("Fitting a line needs at least two points")
    centre = _centroid(points)
    cov = [[0.0] * 3 for _ in range(3)]
    for p in points:
        d = (p.x - centre.x, p.y - centre.y, p.z - centre.z)
        for i in range(3):
            for j in range(3):
                cov[i][j] += d[i] * d[j]
    values, vectors = jacobi_eigen_symmetric(cov)
    largest = max(range(3), key=lambda index: values[index])
    if values[largest] <= 1e-24:
        raise ValueError("Fitting a line needs points that are not all coincident")
    direction = AtomicVector(*(vectors[k][largest] for k in range(3)))
    components = (direction.x, direction.y, direction.z)
    main = max(range(3), key=lambda index: abs(components[index]))
    if components[main] < 0:
        direction = scale(direction, -1.0)
    direction = unit(direction)
    parameters = [dot(sub(p, centre), direction) for p in points]
    start = AtomicPoint(*(getattr(centre, axis) + getattr(direction, axis) * min(parameters) for axis in "xyz"))
    end = AtomicPoint(*(getattr(centre, axis) + getattr(direction, axis) * max(parameters) for axis in "xyz"))
    return AtomicLine(start, end)


def fit_circle(points: Sequence[AtomicPoint]) -> tuple[AtomicCircle, float]:
    """Least-squares circle through ``points`` and the largest radial deviation.

    The circle lies in the least-squares plane of the points (see
    :func:`pyhopper.Utils.Fitting.fit_plane`); the in-plane fit starts from the
    algebraic (Kåsa) solution and is refined by Gauss–Newton to the geometric
    least-squares circle (the one Rhino reports). Fewer than three or collinear
    points raise ``ValueError``.
    """
    if len(points) < 3:
        raise ValueError("Fitting a circle needs at least three points")
    try:
        plane, _ = fit_plane(points)
    except ValueError as error:
        raise ValueError("Fitting a circle needs points that are not all collinear") from error
    flat = [plane_xy(plane, p) for p in points]
    # Kåsa: minimise sum (x² + y² + D x + E y + F)²
    matrix = [[0.0] * 3 for _ in range(3)]
    rhs = [[0.0] for _ in range(3)]
    for x, y in flat:
        row = (x, y, 1.0)
        target = -(x * x + y * y)
        for i in range(3):
            for j in range(3):
                matrix[i][j] += row[i] * row[j]
            rhs[i][0] += row[i] * target
    try:
        (d,), (e,), (f,) = solve_linear_system(matrix, rhs, "Fitting a circle needs points that are not all collinear")
    except ValueError:
        raise ValueError("Fitting a circle needs points that are not all collinear") from None
    cx, cy = -d / 2.0, -e / 2.0
    radius_squared = cx * cx + cy * cy - f
    if radius_squared <= 0.0:
        raise ValueError("Fitting a circle needs points that are not all collinear")
    radius = math.sqrt(radius_squared)
    cx, cy, radius = _refine_circle(flat, cx, cy, radius)
    deviation = max(abs(math.hypot(x - cx, y - cy) - radius) for x, y in flat)
    centre = point_on_plane(plane, cx, cy)
    return AtomicCircle(AtomicPlane(centre, plane.normal, plane.x_axis), radius), deviation


def _refine_circle(flat: Sequence[tuple[float, float]], cx: float, cy: float, radius: float, iterations: int = 50) -> tuple[float, float, float]:
    """Gauss–Newton on the geometric residuals ``|p - c| - r``."""
    for _ in range(iterations):
        jtj = [[0.0] * 3 for _ in range(3)]
        jtr = [[0.0] for _ in range(3)]
        for x, y in flat:
            dist = math.hypot(x - cx, y - cy)
            if dist < 1e-15:
                continue
            residual = dist - radius
            gradient = ((cx - x) / dist, (cy - y) / dist, -1.0)
            for i in range(3):
                jtr[i][0] -= gradient[i] * residual
                for j in range(3):
                    jtj[i][j] += gradient[i] * gradient[j]
        try:
            step = solve_linear_system(jtj, jtr, "singular")
        except ValueError:
            break
        cx += step[0][0]
        cy += step[1][0]
        radius += step[2][0]
        if max(abs(step[0][0]), abs(step[1][0]), abs(step[2][0])) < 1e-13:
            break
    return cx, cy, radius


def incircle(a: AtomicPoint, b: AtomicPoint, c: AtomicPoint) -> tuple[AtomicCircle, AtomicPlane, float]:
    """Inscribed circle of triangle ABC: ``(circle, plane, radius)``.

    The plane sits on the incentre with the triangle's normal ``AB × AC`` and
    its X axis along AB, as Grasshopper reports it.
    """
    ab, ac = sub(b, a), sub(c, a)
    normal = cross(ab, ac)
    if is_zero(normal):
        raise ValueError("InCircle needs a non-degenerate triangle")
    side_a, side_b, side_c = distance(b, c), distance(a, c), distance(a, b)
    perimeter = side_a + side_b + side_c
    centre = AtomicPoint(
        (side_a * a.x + side_b * b.x + side_c * c.x) / perimeter,
        (side_a * a.y + side_b * b.y + side_c * c.y) / perimeter,
        (side_a * a.z + side_b * b.z + side_c * c.z) / perimeter,
    )
    radius = length(normal) / perimeter  # area = |AB × AC| / 2, r = area / semi-perimeter
    plane = AtomicPlane(centre, normal, ab)
    return AtomicCircle(plane, radius), plane, radius


# ── reversal ───────────────────────────────────────────────────────


def reverse_nurbs_curve(curve: AtomicNurbsCurve) -> AtomicNurbsCurve:
    """The same NURBS curve traversed the other way (control points reversed, knots mirrored)."""
    knots = curve.knots
    low, high = knots[0], knots[-1]
    return AtomicNurbsCurve(
        control_points=tuple(reversed(curve.control_points)),
        weights=tuple(reversed(curve.weights)),
        knots=tuple(low + high - knot for knot in reversed(knots)),
        degree=curve.degree,
    )


def _flip_plane(plane: AtomicPlane) -> AtomicPlane:
    return AtomicPlane(plane.origin, scale(plane.normal, -1.0), plane.x_axis)


def reverse_curve(curve):
    """Reverse the direction of any curve atom, keeping its type where the type allows it."""
    if isinstance(curve, AtomicLine):
        return AtomicLine(curve.end, curve.start)
    if isinstance(curve, AtomicPolyline):
        return AtomicPolyline(tuple(reversed(curve.points)))
    if isinstance(curve, AtomicArc):
        # traversing b -> a equals the flipped plane swept from -b to -a
        return AtomicArc(_flip_plane(curve.plane), curve.radius, AtomicInterval(-float(curve.angle.end), -float(curve.angle.start)))
    if isinstance(curve, AtomicCircle):
        return AtomicCircle(_flip_plane(curve.plane), curve.radius)
    if isinstance(curve, AtomicRectangle):
        return AtomicRectangle(_flip_plane(curve.plane), curve.x_size, curve.y_size)
    return reverse_nurbs_curve(as_nurbs_curve(curve))


# ── rebuild (least squares) ────────────────────────────────────────


def uniform_clamped_knots(count: int, degree: int) -> tuple[float, ...]:
    """Rhino-style clamped knots with integer interior spacing: ``0,0,0,1,2,…,n-p,n-p,n-p``."""
    interior = count - degree  # number of spans
    return tuple([0.0] * (degree + 1) + [float(k) for k in range(1, interior)] + [float(interior)] * (degree + 1))


def _basis_row(parameter: float, degree: int, knots: Sequence[float], count: int) -> list[float]:
    span = find_span(degree, knots, count, parameter)
    values = basis_functions(span, parameter, degree, knots)
    row = [0.0] * count
    for offset, value in enumerate(values):
        row[span - degree + offset] = value
    return row


def rebuild_curve(curve, count: int, degree: int | None = None, keep_tangents: bool = False, samples: int = 200) -> AtomicNurbsCurve:
    """Non-rational least-squares rebuild with ``count`` control points and ``degree``.

    The curve is sampled uniformly in parameter; the end control points are
    pinned to the curve ends and, with ``keep_tangents``, the second and
    penultimate control points slide along the end tangents (one scalar each).
    ``degree`` defaults to the source curve's degree.
    """
    source = as_nurbs_curve(curve)
    p = int(source.degree if degree is None else degree)
    n = int(count)
    if p < 1:
        raise ValueError("Rebuild degree must be at least 1")
    if n < p + 1:
        raise ValueError(f"Rebuild needs at least {p + 1} control points for degree {p}")
    keep_tangents = bool(keep_tangents) and n >= 4
    knots = uniform_clamped_knots(n, p)
    span = knots[-1]
    domain_start, domain_end = curve_domain_of(curve)
    start_point = curve_point_at(curve, domain_start)
    end_point = curve_point_at(curve, domain_end)
    pinned = {0: (start_point.x, start_point.y, start_point.z), n - 1: (end_point.x, end_point.y, end_point.z)}
    # sliding control points: index -> (anchor, direction); the unknown is the scalar along the direction
    sliding: dict[int, tuple[tuple[float, float, float], AtomicVector]] = {}
    if keep_tangents:
        sliding[1] = (pinned[0], unit(curve_tangent_at(curve, domain_start)))
        sliding[n - 2] = (pinned[n - 1], scale(unit(curve_tangent_at(curve, domain_end)), -1.0))
    free = [index for index in range(n) if index not in pinned and index not in sliding]
    slide_order = sorted(sliding)
    unknowns = 3 * len(free) + len(slide_order)
    normal = [[0.0] * unknowns for _ in range(unknowns)]
    rhs = [0.0] * unknowns
    m = max(samples, 4 * n)
    for index in range(m + 1):
        fraction = index / m
        point = curve_point_at(curve, domain_start + (domain_end - domain_start) * fraction)
        row = _basis_row(span * fraction, p, knots, n)
        for axis, target in enumerate((point.x, point.y, point.z)):
            residual = target
            for pin, coordinates in pinned.items():
                residual -= row[pin] * coordinates[axis]
            for slide in slide_order:
                anchor, _ = sliding[slide]
                residual -= row[slide] * anchor[axis]
            coefficients: list[tuple[int, float]] = [(3 * position + axis, row[free_index]) for position, free_index in enumerate(free) if row[free_index]]
            for position, slide in enumerate(slide_order):
                _, direction = sliding[slide]
                component = (direction.x, direction.y, direction.z)[axis]
                if row[slide] and component:
                    coefficients.append((3 * len(free) + position, row[slide] * component))
            for i, ci in coefficients:
                rhs[i] += ci * residual
                for j, cj in coefficients:
                    normal[i][j] += ci * cj
    solution = [value[0] for value in solve_linear_system(normal, [[value] for value in rhs], "Rebuild could not fit the curve")] if unknowns else []
    controls: list[AtomicPoint] = [AtomicPoint(0.0, 0.0, 0.0)] * n
    for pin, coordinates in pinned.items():
        controls[pin] = AtomicPoint(*coordinates)
    for position, free_index in enumerate(free):
        controls[free_index] = AtomicPoint(*solution[3 * position: 3 * position + 3])
    for position, slide in enumerate(slide_order):
        anchor, direction = sliding[slide]
        scalar = solution[3 * len(free) + position]
        controls[slide] = AtomicPoint(anchor[0] + direction.x * scalar, anchor[1] + direction.y * scalar, anchor[2] + direction.z * scalar)
    return AtomicNurbsCurve(tuple(controls), tuple(1.0 for _ in controls), knots, p)


# ── catenary ───────────────────────────────────────────────────────


def catenary_points(a: AtomicPoint, b: AtomicPoint, chain_length: float, gravity: AtomicVector, samples: int = 50) -> list[AtomicPoint] | None:
    """``samples`` points of the catenary of length ``chain_length`` hanging from A to B under ``gravity``.

    Points are spaced uniformly along the horizontal span (Grasshopper's 50-point
    polyline). Returns ``None`` when the chain is taut (length <= distance) so the
    caller can fall back to a straight line; a purely vertical span raises.
    """
    down = unit(gravity)
    if is_zero(down):
        raise ValueError("Catenary needs a non-zero gravity vector")
    chord = sub(b, a)
    drop = dot(chord, down)  # how far B lies below A along gravity
    horizontal = sub(chord, scale(down, drop))
    span = length(horizontal)
    total = float(chain_length)
    if total <= length(chord) + 1e-12:
        return None
    if span < 1e-12:
        raise ValueError("Catenary needs end points that are not on top of each other")
    across = unit(horizontal)
    # solve 2 a sinh(span / 2a) = sqrt(L² - drop²) for the catenary parameter a
    target = math.sqrt(max(total * total - drop * drop, 0.0))
    lo, hi = 1e-9, 1.0
    while 2.0 * hi * math.sinh(span / (2.0 * hi)) > target:
        hi *= 2.0
        if hi > 1e12:
            break
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 2.0 * mid * math.sinh(span / (2.0 * mid)) > target:
            lo = mid
        else:
            hi = mid
    a_param = 0.5 * (lo + hi)
    # vertex offset so the curve passes through both ends: y(x) = a cosh((x - x0)/a) + c (y measured against gravity)
    # y(0) = 0, y(span) = -drop  ->  cosh((span - x0)/a) - cosh(-x0/a) = -drop / a
    x0 = a_param * math.asinh(-drop / (2.0 * a_param * math.sinh(span / (2.0 * a_param)))) + span / 2.0
    offset = -a_param * math.cosh(-x0 / a_param)
    points = []
    for index in range(samples):
        x = span * index / (samples - 1)
        y = a_param * math.cosh((x - x0) / a_param) + offset  # negative: below the start
        points.append(AtomicPoint(
            a.x + across.x * x - down.x * y,
            a.y + across.y * x - down.y * y,
            a.z + across.z * x - down.z * y,
        ))
    return points


# ── polyline approximation ─────────────────────────────────────────


def _segments_for_arc(radius: float, sweep: float, tolerance: float, min_edge: float | None, max_edge: float | None) -> int:
    count = 1
    while radius * (1.0 - math.cos(sweep / (2 * count))) > tolerance and count < 10000:
        count += 1
    if max_edge is not None and max_edge > 0:
        while 2.0 * radius * math.sin(sweep / (2 * count)) > max_edge and count < 10000:
            count += 1
    if min_edge is not None and min_edge > 0:
        while count > 1 and 2.0 * radius * math.sin(sweep / (2 * count)) < min_edge:
            count -= 1
    return count


def curve_to_polyline(curve, tolerance: float, angle_tolerance: float = 0.0, min_edge: float | None = None, max_edge: float | None = None) -> AtomicPolyline:
    """Polyline approximation of a curve atom within ``tolerance``.

    Lines and polylines pass through unchanged. Arcs and circles use the exact
    chord-sagitta count (the smallest segment count whose sagitta is within the
    tolerance, then more for ``max_edge`` and fewer for ``min_edge``) — this
    reproduces Grasshopper's counts. Other curves are subdivided recursively
    until every chord's midpoint deviation is within the tolerance.
    """
    if isinstance(curve, AtomicPolyline):
        return curve
    if isinstance(curve, AtomicLine):
        return AtomicPolyline((curve.start, curve.end))
    tol = float(tolerance) if tolerance and tolerance > 0 else 0.001
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        sweep = 2.0 * math.pi if isinstance(curve, AtomicCircle) else abs(float(curve.angle.end) - float(curve.angle.start))
        count = _segments_for_arc(float(curve.radius), sweep, tol, min_edge, max_edge)
        start, end = curve_domain_of(curve)
        points = [curve_point_at(curve, start + (end - start) * k / count) for k in range(count + 1)]
        return AtomicPolyline(tuple(points))
    start, end = curve_domain_of(curve)
    parameters = [start, end]

    def refine(t0: float, t1: float, depth: int) -> list[float]:
        mid = 0.5 * (t0 + t1)
        p0, p1, pm = curve_point_at(curve, t0), curve_point_at(curve, t1), curve_point_at(curve, mid)
        chord_mid = AtomicPoint((p0.x + p1.x) / 2, (p0.y + p1.y) / 2, (p0.z + p1.z) / 2)
        too_long = max_edge is not None and max_edge > 0 and distance(p0, p1) > max_edge
        if depth < 12 and (distance(pm, chord_mid) > tol or too_long):
            return refine(t0, mid, depth + 1) + refine(mid, t1, depth + 1)[1:]
        return [t0, t1]

    parameters = refine(start, end, 0)
    if min_edge is not None and min_edge > 0:
        kept = [parameters[0]]
        for parameter in parameters[1:-1]:
            if distance(curve_point_at(curve, kept[-1]), curve_point_at(curve, parameter)) >= min_edge:
                kept.append(parameter)
        kept.append(parameters[-1])
        parameters = kept
    return AtomicPolyline(tuple(curve_point_at(curve, parameter) for parameter in parameters))
