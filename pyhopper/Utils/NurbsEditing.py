"""NurbsEditing - knot insertion, splitting, degree elevation, joining and
extension of NURBS curves, plus knot insertion / sub-surfaces for surfaces
(the K2 kernel of the component roadmap).

Everything works on homogeneous control points ``(w·x, w·y, w·z, w)`` so
rational curves are handled exactly. Curve atoms carry their full knot vector;
surfaces carry unique knots plus multiplicities (see ``Utils/Nurbs.py``).
"""

from __future__ import annotations

from typing import Sequence

from pyhopper.Core.Atoms import AtomicNurbsCurve, AtomicPoint, AtomicSurface
from pyhopper.Utils.Nurbs import (
    TOLERANCE,
    basis_row,
    collapse_knots,
    curve_domain,
    expand_knots,
    find_span,
    greville_abscissae,
    solve_linear_system,
)

Homogeneous = list[float]


# ── homogeneous helpers ────────────────────────────────────────────


def _homogeneous(curve: AtomicNurbsCurve) -> list[Homogeneous]:
    weights = curve.weights if len(curve.weights) == len(curve.control_points) else tuple(1.0 for _ in curve.control_points)
    return [[p.x * w, p.y * w, p.z * w, w] for p, w in zip(curve.control_points, weights)]


def _from_homogeneous(points: Sequence[Homogeneous], knots: Sequence[float], degree: int) -> AtomicNurbsCurve:
    control_points = []
    weights = []
    for x, y, z, w in points:
        if abs(w) <= TOLERANCE:
            raise ValueError("NURBS control point has a zero weight")
        control_points.append(AtomicPoint(x / w, y / w, z / w))
        weights.append(float(w))
    return AtomicNurbsCurve(tuple(control_points), tuple(weights), tuple(float(k) for k in knots), int(degree))


def _knot_multiplicity(knots: Sequence[float], value: float, tolerance: float = 1e-12) -> int:
    return sum(1 for knot in knots if abs(knot - value) <= tolerance)


def _insert_knot_homogeneous(points: list[Homogeneous], knots: list[float], degree: int, value: float, times: int) -> tuple[list[Homogeneous], list[float]]:
    """Boehm's knot insertion (A5.1) on homogeneous points; returns the refined points and knots."""
    for _ in range(times):
        n = len(points)
        span = find_span(degree, knots, n, value)
        new_points: list[Homogeneous] = points[: span - degree + 1]
        for i in range(span - degree + 1, span + 1):
            denominator = knots[i + degree] - knots[i]
            alpha = 0.0 if abs(denominator) <= TOLERANCE else (value - knots[i]) / denominator
            new_points.append([alpha * a + (1.0 - alpha) * b for a, b in zip(points[i], points[i - 1])])
        new_points.extend(points[span:])
        knots = knots[: span + 1] + [value] + knots[span + 1 :]
        points = new_points
    return points, knots


# ── knot insertion, splitting, sub-curves ──────────────────────────


def insert_knot(curve: AtomicNurbsCurve, value: float, times: int = 1) -> AtomicNurbsCurve:
    """Insert *value* into the knot vector *times* times (geometry unchanged); capped at multiplicity ``degree``."""
    start, end = curve_domain(curve)
    if not start - 1e-12 <= value <= end + 1e-12:
        raise ValueError("Knot to insert lies outside the curve domain")
    degree = int(curve.degree)
    current = _knot_multiplicity(curve.knots, value)
    allowed = max(0, min(int(times), degree - current))
    if allowed == 0:
        return curve
    points, knots = _insert_knot_homogeneous(_homogeneous(curve), [float(k) for k in curve.knots], degree, float(value), allowed)
    return _from_homogeneous(points, knots, degree)


def _clamped_at(curve: AtomicNurbsCurve, value: float) -> tuple[list[Homogeneous], list[float]]:
    """Homogeneous points and knots with *value* raised to multiplicity ``degree``."""
    degree = int(curve.degree)
    points, knots = _homogeneous(curve), [float(k) for k in curve.knots]
    missing = degree - _knot_multiplicity(knots, value)
    if missing > 0:
        points, knots = _insert_knot_homogeneous(points, knots, degree, float(value), missing)
    return points, knots


def sub_nurbs_curve(curve: AtomicNurbsCurve, start: float, end: float) -> AtomicNurbsCurve:
    """The portion of *curve* over ``[start, end]`` (clamped to the domain), keeping its parameterisation."""
    domain_start, domain_end = curve_domain(curve)
    a, b = max(domain_start, min(float(start), float(end))), min(domain_end, max(float(start), float(end)))
    if b - a <= 1e-12:
        raise ValueError("Sub-curve interval is empty")
    degree = int(curve.degree)
    points, knots = _clamped_at(curve, a)
    if b < domain_end - 1e-12:
        missing = degree - _knot_multiplicity(knots, b)
        if missing > 0:
            points, knots = _insert_knot_homogeneous(points, knots, degree, b, missing)
    first, last = _window(knots, degree, a, b)
    piece_knots = [a] * (degree + 1) + [k for k in knots if a + 1e-12 < k < b - 1e-12] + [b] * (degree + 1)
    return _from_homogeneous(points[first : last + 1], piece_knots, degree)


def _window(knots: Sequence[float], degree: int, a: float, b: float) -> tuple[int, int]:
    """Indices of the first and last control point active on ``(a, b)`` once ``a`` and ``b`` carry
    multiplicity ``degree`` (or sit at the clamped ends): the piece's control points."""
    last_a = max(i for i in range(len(knots)) if abs(knots[i] - a) <= 1e-12)
    first_b = min(i for i in range(len(knots)) if abs(knots[i] - b) <= 1e-12)
    return last_a - degree, first_b - 1


def split_nurbs_curve(curve: AtomicNurbsCurve, parameter: float) -> tuple[AtomicNurbsCurve, AtomicNurbsCurve]:
    """Split at *parameter* into two curves that keep the original parameterisation."""
    start, end = curve_domain(curve)
    t = float(parameter)
    if not start + 1e-12 < t < end - 1e-12:
        raise ValueError("Split parameter must lie strictly inside the curve domain")
    return sub_nurbs_curve(curve, start, t), sub_nurbs_curve(curve, t, end)


# ── degree elevation and joining ───────────────────────────────────


def _interpolate_in_space(curve: AtomicNurbsCurve, knots: list[float], degree: int) -> AtomicNurbsCurve:
    """Re-express *curve* exactly in the spline space (knots, degree) by collocation at the Greville
    abscissae (the space must contain the curve)."""
    count = len(knots) - degree - 1
    parameters = greville_abscissae(knots, degree, count)
    matrix = [basis_row(t, degree, knots, count) for t in parameters]
    samples = [_homogeneous_point(curve, t) for t in parameters]
    return _from_homogeneous(solve_linear_system(matrix, samples, "Degenerate spline space"), knots, degree)


def _homogeneous_point(curve: AtomicNurbsCurve, parameter: float) -> Homogeneous:
    points = _homogeneous(curve)
    row = basis_row(parameter, int(curve.degree), curve.knots, len(points))
    return [sum(row[i] * points[i][axis] for i in range(len(points))) for axis in range(4)]


def elevate_degree(curve: AtomicNurbsCurve, target: int) -> AtomicNurbsCurve:
    """Raise the degree to *target* without changing the geometry (interior knot multiplicities grow
    by the elevation so the continuity at every knot is preserved)."""
    degree = int(curve.degree)
    target = int(target)
    if target <= degree:
        return curve
    start, end = curve_domain(curve)
    unique, mults = collapse_knots(curve.knots)
    raise_by = target - degree
    new_knots: list[float] = []
    for knot, mult in zip(unique, mults):
        if knot <= start + 1e-12 or knot >= end - 1e-12:
            new_knots.extend([float(knot)] * (target + 1))
        else:
            new_knots.extend([float(knot)] * (mult + raise_by))
    return _interpolate_in_space(curve, new_knots, target)


def redomain(curve: AtomicNurbsCurve, start: float, end: float) -> AtomicNurbsCurve:
    """Affine knot remap onto ``[start, end]``."""
    a, b = curve_domain(curve)
    scale = (float(end) - float(start)) / (b - a)
    return AtomicNurbsCurve(curve.control_points, curve.weights, tuple(float(start) + (float(k) - a) * scale for k in curve.knots), curve.degree)


def join_nurbs_curves(curves: Sequence[AtomicNurbsCurve], breaks: Sequence[float]) -> AtomicNurbsCurve:
    """Concatenate end-to-end curves into one NURBS curve on the parameter breaks ``breaks`` (one more
    than the curves): every piece is elevated to the common degree and re-domained onto its
    interval; the joints carry knots of multiplicity ``degree`` (C0)."""
    if len(breaks) != len(curves) + 1:
        raise ValueError("join_nurbs_curves needs one break more than curves")
    degree = max(int(c.degree) for c in curves)
    pieces = [redomain(elevate_degree(c, degree), breaks[i], breaks[i + 1]) for i, c in enumerate(curves)]
    points: list[Homogeneous] = []
    knots: list[float] = []
    for index, piece in enumerate(pieces):
        piece_points = _homogeneous(piece)
        piece_knots = [float(k) for k in piece.knots]
        if index == 0:
            points.extend(piece_points)
            knots.extend(piece_knots[: len(piece_knots) - 1])  # drop one end knot: the joint has multiplicity degree
        else:
            # share the joint control point (average the two coincident ends in homogeneous form)
            shared = [(a + b) / 2.0 for a, b in zip(points[-1], piece_points[0])]
            points[-1] = shared
            points.extend(piece_points[1:])
            knots.extend(piece_knots[degree + 1 : len(piece_knots) - 1])
    knots.append(float(breaks[-1]))
    return _from_homogeneous(points, knots, degree)


# ── smooth extension ───────────────────────────────────────────────


def extend_nurbs_domain(curve: AtomicNurbsCurve, new_start: float, new_end: float) -> AtomicNurbsCurve:
    """Extend the curve polynomially (Rhino's *smooth* extension): the end spans are extrapolated onto
    ``[new_start, new_end]`` and the end control points re-solved so the curve is unchanged on its old
    domain (only ``new_start <= start`` / ``new_end >= end`` extend; the others leave that end alone)."""
    degree = int(curve.degree)
    start, end = curve_domain(curve)
    points, knots = _homogeneous(curve), [float(k) for k in curve.knots]
    count = len(points)
    if new_start < start - 1e-12:
        knots = [float(new_start)] * (degree + 1) + knots[degree + 1 :]
        points = _resolve_end(curve, points, knots, degree, list(range(0, degree + 1)), (start, knots[degree + 1]))
    if new_end > end + 1e-12:
        knots = knots[: count] + [float(new_end)] * (degree + 1)
        points = _resolve_end(curve, points, knots, degree, list(range(count - degree - 1, count)), (knots[count - 1], end))
    return _from_homogeneous(points, knots, degree)


def _resolve_end(curve: AtomicNurbsCurve, points: list[Homogeneous], knots: list[float], degree: int, unknown: list[int], window: tuple[float, float]) -> list[Homogeneous]:
    """Re-solve the control points ``unknown`` so the spline on *knots* reproduces *curve* on *window*."""
    count = len(points)
    a, b = window
    parameters = [a + (b - a) * (i + 0.5) / len(unknown) for i in range(len(unknown))]
    matrix, values = [], []
    for t in parameters:
        row = basis_row(t, degree, knots, count)
        target = _homogeneous_point(curve, t)
        known = [sum(row[i] * points[i][axis] for i in range(count) if i not in unknown) for axis in range(4)]
        matrix.append([row[i] for i in unknown])
        values.append([target[axis] - known[axis] for axis in range(4)])
    solved = solve_linear_system(matrix, values, "Curve extension is degenerate")
    result = [p[:] for p in points]
    for index, value in zip(unknown, solved):
        result[index] = value
    return result


# ── surfaces ───────────────────────────────────────────────────────


def _surface_rows_homogeneous(surface: AtomicSurface) -> list[list[Homogeneous]]:
    return [[[p.x * w, p.y * w, p.z * w, w] for p, w in zip(row, weights)] for row, weights in zip(surface.poles, surface.weights)]


def _surface_from_rows(rows: list[list[Homogeneous]], u_knots: Sequence[float], v_knots: Sequence[float], u_degree: int, v_degree: int) -> AtomicSurface:
    poles, weights = [], []
    for row in rows:
        pole_row, weight_row = [], []
        for x, y, z, w in row:
            pole_row.append(AtomicPoint(x / w, y / w, z / w))
            weight_row.append(float(w))
        poles.append(tuple(pole_row))
        weights.append(tuple(weight_row))
    uk, um = collapse_knots(u_knots)
    vk, vm = collapse_knots(v_knots)
    return AtomicSurface(poles=tuple(poles), weights=tuple(weights), u_knots=uk, v_knots=vk, u_mults=um, v_mults=vm, u_degree=u_degree, v_degree=v_degree)


def _clamp_direction(rows: list[list[Homogeneous]], knots: list[float], degree: int, value: float, along_u: bool) -> tuple[list[list[Homogeneous]], list[float]]:
    missing = degree - _knot_multiplicity(knots, value)
    if missing <= 0:
        return rows, knots
    if along_u:
        new_rows = []
        for row in rows:
            new_row, new_knots = _insert_knot_homogeneous(row, list(knots), degree, value, missing)
            new_rows.append(new_row)
        return new_rows, new_knots
    columns = [[row[u] for row in rows] for u in range(len(rows[0]))]
    new_columns = []
    for column in columns:
        new_column, new_knots = _insert_knot_homogeneous(column, list(knots), degree, value, missing)
        new_columns.append(new_column)
    return [[new_columns[u][v] for u in range(len(new_columns))] for v in range(len(new_columns[0]))], new_knots


def sub_surface(surface: AtomicSurface, u_domain: tuple[float, float], v_domain: tuple[float, float]) -> AtomicSurface:
    """The surface patch over ``u_domain × v_domain`` (each clamped to the surface domain), keeping the
    parameterisation (Grasshopper's Isotrim)."""
    from pyhopper.Utils.Nurbs import surface_degrees, surface_domain

    (u0, u1), (v0, v1) = surface_domain(surface)
    u_degree, v_degree = surface_degrees(surface)
    ua, ub = max(u0, min(u_domain)), min(u1, max(u_domain))
    va, vb = max(v0, min(v_domain)), min(v1, max(v_domain))
    if ub - ua <= 1e-12 or vb - va <= 1e-12:
        raise ValueError("Sub-surface domain is empty")
    rows = _surface_rows_homogeneous(surface)
    u_knots, v_knots = [float(k) for k in expand_knots(surface.u_knots, surface.u_mults)], [float(k) for k in expand_knots(surface.v_knots, surface.v_mults)]
    for value in (ua, ub):
        if u0 + 1e-12 < value < u1 - 1e-12:
            rows, u_knots = _clamp_direction(rows, u_knots, u_degree, value, True)
    for value in (va, vb):
        if v0 + 1e-12 < value < v1 - 1e-12:
            rows, v_knots = _clamp_direction(rows, v_knots, v_degree, value, False)
    u_first, u_last = _window(u_knots, u_degree, ua, ub)
    v_first, v_last = _window(v_knots, v_degree, va, vb)
    new_u = [ua] * (u_degree + 1) + [k for k in u_knots if ua + 1e-12 < k < ub - 1e-12] + [ub] * (u_degree + 1)
    new_v = [va] * (v_degree + 1) + [k for k in v_knots if va + 1e-12 < k < vb - 1e-12] + [vb] * (v_degree + 1)
    patch = [row[u_first : u_last + 1] for row in rows[v_first : v_last + 1]]
    return _surface_from_rows(patch, new_u, new_v, u_degree, v_degree)
