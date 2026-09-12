"""Nurbs - the single home for B-spline / NURBS kernel math.

Knot vectors, span search, Cox–de Boor basis functions, curve and surface
evaluation, profile extraction and knot-aware parameter sampling live here.
``Utils/Curves.py``, ``Utils/Surfaces.py``, the GLB exporter and the surface
components all build on these functions instead of carrying private copies.

Conventions
-----------
* Curve atoms (`AtomicNurbsCurve`) store the **full** knot vector
  (``len == point_count + degree + 1``); surfaces store **unique knots plus
  multiplicities** (OCCT style). :func:`expand_knots` / :func:`collapse_knots`
  convert between the two.
* Parameters are always in the knot domain; evaluators clamp into it.
* Surface pole grids are indexed ``poles[v][u]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from pyhopper.Core.Atoms import (
    AtomicNurbsCurve,
    AtomicPoint,
    AtomicSurface,
    _collapse_repeated_knots,
    _open_uniform_bspline_data,
)

TOLERANCE = 1e-12

# Interior samples per knot span used by tessellation and integration, by degree.
SUBDIVISIONS_PER_SPAN = {1: 1, 2: 16, 3: 12}


# ── Knot vectors ────────────────────────────────────────────────────


def expand_knots(knots: Sequence[float], mults: Sequence[int]) -> tuple[float, ...]:
    """Unique knots + multiplicities → full knot vector of floats."""
    expanded: list[float] = []
    for knot, mult in zip(knots, mults):
        expanded.extend([float(knot)] * int(mult))
    return tuple(expanded)


def collapse_knots(knots: Sequence[float], tolerance: float = 0.0) -> tuple[tuple[float, ...], tuple[int, ...]]:
    """Full knot vector → (unique knots, multiplicities).

    With ``tolerance == 0`` equality is exact (the atom-level rule); a positive
    tolerance merges knots closer than that distance.
    """
    if tolerance <= 0.0:
        return _collapse_repeated_knots(tuple(knots))
    if not knots:
        return (), ()
    unique_knots = [knots[0]]
    multiplicities = [1]
    for knot in knots[1:]:
        if abs(knot - unique_knots[-1]) <= tolerance:
            multiplicities[-1] += 1
        else:
            unique_knots.append(knot)
            multiplicities.append(1)
    return tuple(unique_knots), tuple(multiplicities)


def open_uniform_knots(point_count: int, degree: int) -> tuple[tuple[float, ...], tuple[int, ...], int]:
    """Clamped open-uniform knots on [0, 1] as (unique knots, mults, clamped degree)."""
    return _open_uniform_bspline_data(point_count, degree)


def interpolation_knots(parameters: Sequence[float], degree: int) -> tuple[float, ...]:
    """Averaged interior knots for global interpolation (The NURBS Book, eq. 9.8)."""
    interior = tuple(
        sum(parameters[index : index + degree]) / degree
        for index in range(1, len(parameters) - degree)
    )
    return (parameters[0],) * (degree + 1) + interior + (parameters[-1],) * (degree + 1)


def rhino_knots(knots: Sequence[float]) -> tuple[float, ...]:
    """Rhino/Grasshopper knot list: the full vector without its two superfluous end knots."""
    return tuple(float(knot) for knot in knots[1:-1])


def from_rhino_knots(knots: Sequence[float]) -> tuple[float, ...]:
    """Inverse of :func:`rhino_knots` — re-add the duplicated end knots."""
    values = [float(knot) for knot in knots]
    if not values:
        return ()
    return (values[0], *values, values[-1])


def greville_abscissae(knots: Sequence[float], degree: int, point_count: int) -> list[float]:
    """Greville parameter of every control point (average of ``degree`` consecutive knots)."""
    return [sum(knots[index + 1 : index + degree + 1]) / degree for index in range(point_count)]


# ── Spans and basis functions ───────────────────────────────────────


def find_span(degree: int, knots: Sequence[float], point_count: int, parameter: float) -> int:
    """Index of the knot span containing *parameter* (binary search, clamped ends)."""
    if parameter >= knots[point_count]:
        return point_count - 1
    if parameter <= knots[degree]:
        return degree

    low = degree
    high = point_count
    span = (low + high) // 2
    while parameter < knots[span] or parameter >= knots[span + 1]:
        if parameter < knots[span]:
            high = span
        else:
            low = span
        span = (low + high) // 2
    return span


def basis_functions(span: int, parameter: float, degree: int, knots: Sequence[float]) -> list[float]:
    """The ``degree + 1`` non-zero B-spline basis values at *parameter* (Cox–de Boor)."""
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
            term = 0.0 if abs(denominator) <= TOLERANCE else basis[index] / denominator
            basis[index] = saved + right[index + 1] * term
            saved = left[order - index] * term
        basis[order] = saved

    return basis


def basis_row(parameter: float, degree: int, knots: Sequence[float], point_count: int) -> list[float]:
    """Full-length basis row (one entry per control point) at *parameter*."""
    span = find_span(degree, knots, point_count, parameter)
    row = [0.0] * point_count
    for local_index, value in enumerate(basis_functions(span, parameter, degree, knots)):
        row[span - degree + local_index] = value
    return row


def basis_matrix(parameters: Sequence[float], knots: Sequence[float], degree: int) -> list[list[float]]:
    """Collocation matrix for global interpolation at *parameters*."""
    point_count = len(parameters)
    return [basis_row(parameter, degree, knots, point_count) for parameter in parameters]


def solve_linear_system(
    matrix: list[list[float]],
    values: list[list[float]],
    message: str = "Linear system is singular",
) -> list[list[float]]:
    """Gauss–Jordan elimination with partial pivoting; raises ``ValueError(message)`` when singular."""
    size = len(matrix)
    augmented = [matrix[row][:] + values[row][:] for row in range(size)]
    value_count = len(values[0])
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= TOLERANCE:
            raise ValueError(message)
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if abs(factor) <= TOLERANCE:
                continue
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column])
            ]
    return [row[size : size + value_count] for row in augmented]


# ── Curve profiles and evaluation ───────────────────────────────────


@dataclass(frozen=True)
class CurveProfile:
    """Surface-ready view of a NURBS curve: poles, weights, unique knots, mults, degree."""

    poles: tuple[AtomicPoint, ...]
    weights: tuple[float, ...]
    knots: tuple[float, ...]
    mults: tuple[int, ...]
    degree: int


def curve_profile(curve: AtomicNurbsCurve, owner: str = "Surface", tolerance: float = 0.0) -> CurveProfile:
    """Extract pole/weight/knot data from a NURBS curve for tensor-product construction.

    Accepts either a full knot vector or a unique-knot sequence; missing knots
    default to clamped open-uniform. *owner* names the calling component in
    error messages.
    """
    if len(curve.control_points) < 2:
        raise ValueError(f"{owner} requires curves with at least two control points")

    degree = max(1, min(int(curve.degree), len(curve.control_points) - 1))
    weights = (
        curve.weights
        if len(curve.weights) == len(curve.control_points)
        else tuple(1.0 for _ in curve.control_points)
    )

    if not curve.knots:
        knots, mults, degree = open_uniform_knots(len(curve.control_points), degree)
    else:
        raw_knots = tuple(float(knot) for knot in curve.knots)
        expected_full = len(curve.control_points) + degree + 1
        expected_unique = len(curve.control_points) - degree + 1
        if len(raw_knots) == expected_full:
            knots, mults = collapse_knots(raw_knots, tolerance)
        elif len(raw_knots) == expected_unique:
            knots = raw_knots
            mults = tuple(
                degree + 1 if index in (0, len(raw_knots) - 1) else 1
                for index in range(len(raw_knots))
            )
        else:
            raise ValueError(
                f"{owner} could not interpret a profile knot vector; expected either "
                "a full knot vector or a unique-knot sequence matching its control point count."
            )
    return CurveProfile(curve.control_points, weights, knots, mults, degree)


def curve_domain(curve: AtomicNurbsCurve) -> tuple[float, float]:
    """Active parameter interval of a valid NURBS curve."""
    point_count = len(curve.control_points)
    degree = int(curve.degree)
    if point_count < 2 or degree < 1 or degree >= point_count:
        raise ValueError("NURBS curve has an invalid control-point count or degree")
    if len(curve.knots) != point_count + degree + 1:
        raise ValueError("NURBS curve knot count must equal point count + degree + 1")
    return float(curve.knots[degree]), float(curve.knots[point_count])


def curve_point(curve: AtomicNurbsCurve, parameter: float) -> AtomicPoint:
    """Evaluate a rational curve at one parameter (clamped into the domain)."""
    start, end = curve_domain(curve)
    value = min(end, max(start, float(parameter)))
    point_count = len(curve.control_points)
    span = find_span(curve.degree, curve.knots, point_count, value)
    basis = basis_functions(span, value, curve.degree, curve.knots)
    weights = (
        curve.weights
        if len(curve.weights) == point_count
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


# ── Surface evaluation ──────────────────────────────────────────────


def expanded_surface_knots(surface: AtomicSurface) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Full U and V knot vectors of a surface."""
    return expand_knots(surface.u_knots, surface.u_mults), expand_knots(surface.v_knots, surface.v_mults)


def surface_degrees(surface: AtomicSurface) -> tuple[int, int]:
    """Effective (u_degree, v_degree), clamped to the pole counts."""
    v_count = len(surface.poles)
    u_count = len(surface.poles[0])
    return max(1, min(int(surface.u_degree), u_count - 1)), max(1, min(int(surface.v_degree), v_count - 1))


def surface_domain(surface: AtomicSurface) -> tuple[tuple[float, float], tuple[float, float]]:
    """((u_start, u_end), (v_start, v_end)) in the knot domain."""
    v_count = len(surface.poles)
    u_count = len(surface.poles[0])
    u_knots, v_knots = expanded_surface_knots(surface)
    u_degree, v_degree = surface_degrees(surface)
    return (u_knots[u_degree], u_knots[u_count]), (v_knots[v_degree], v_knots[v_count])


def surface_point_xyz(surface: AtomicSurface, u: float, v: float) -> tuple[float, float, float]:
    """Evaluate a rational surface at (u, v), clamped into the domain; returns an xyz tuple."""
    v_count = len(surface.poles)
    u_count = len(surface.poles[0])
    u_knots, v_knots = expanded_surface_knots(surface)
    u_degree, v_degree = surface_degrees(surface)
    uu = max(u_knots[u_degree], min(u_knots[u_count], float(u)))
    vv = max(v_knots[v_degree], min(v_knots[v_count], float(v)))
    u_span = find_span(u_degree, u_knots, u_count, uu)
    v_span = find_span(v_degree, v_knots, v_count, vv)
    u_basis = basis_functions(u_span, uu, u_degree, u_knots)
    v_basis = basis_functions(v_span, vv, v_degree, v_knots)

    x = y = z = total_weight = 0.0
    for v_index, v_value in enumerate(v_basis):
        row = v_span - v_degree + v_index
        for u_index, u_value in enumerate(u_basis):
            column = u_span - u_degree + u_index
            point = surface.poles[row][column]
            coefficient = u_value * v_value * surface.weights[row][column]
            x += coefficient * point.x
            y += coefficient * point.y
            z += coefficient * point.z
            total_weight += coefficient
    if abs(total_weight) < 1e-12:
        raise ValueError("Surface evaluation produced a zero rational weight")
    return x / total_weight, y / total_weight, z / total_weight


def surface_point(surface: AtomicSurface, u: float, v: float) -> AtomicPoint:
    """Evaluate a surface at (u, v) as an ``AtomicPoint``."""
    return AtomicPoint(*surface_point_xyz(surface, u, v))


# ── Sampling ────────────────────────────────────────────────────────


def span_parameter_samples(
    knots: Sequence[float],
    mults: Sequence[int],
    degree: int,
    subdivisions_per_span: dict[int, int] | None = None,
) -> list[float]:
    """Parameter samples that respect knot-span boundaries.

    Every unique knot in the active range is a sample; each span gets
    ``subdivisions_per_span[degree]`` interior steps (default table
    :data:`SUBDIVISIONS_PER_SPAN`, else ``max(6, 2 * degree)``).
    """
    table = SUBDIVISIONS_PER_SPAN if subdivisions_per_span is None else subdivisions_per_span
    full_knots = expand_knots(knots, mults)
    point_count = len(full_knots) - degree - 1
    start = full_knots[degree]
    end = full_knots[point_count]
    if end <= start:
        return [start, end]

    boundaries = [start]
    for knot in full_knots[degree + 1 : point_count + 1]:
        if knot > boundaries[-1]:
            boundaries.append(knot)
    if boundaries[-1] < end:
        boundaries.append(end)

    subdivisions = table.get(degree, max(6, degree * 2))
    samples: list[float] = []
    for span_start, span_end in zip(boundaries, boundaries[1:]):
        samples.extend(
            span_start + (span_end - span_start) * index / subdivisions
            for index in range(subdivisions)
        )
    samples.append(boundaries[-1])
    return samples
