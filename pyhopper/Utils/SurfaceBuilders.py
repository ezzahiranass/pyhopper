"""Surface constructions and measures for the Surface components (Grasshopper conventions).

* ``plane_surface`` — a degree-1 patch whose knots *are* the size domains.
* ``sum_surface`` — the translational surface ``A(u) + B(v) - B(start)`` with
  A's knots in U and B's knots in V; weights multiply.
* ``extrude_to_point`` — a ruled surface from a curve (V, its own knots) to an
  apex (U, degree 1, domain = distance from the curve start to the apex).
* ``surface_control_points`` — control points, weights and Greville (u, v, 0)
  points in Grasshopper's order (u outer, v inner) plus the counts.
* ``surface_dimensions`` — the longest control-polygon length in each direction,
  which is what Grasshopper reports as the surface's approximate dimensions.

All verified against Grasshopper 8 with the headless oracle.
"""

from __future__ import annotations

import math

from typing import Sequence

from pyhopper.Core.Atoms import AtomicInterval, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicSurface, AtomicVector
from pyhopper.Utils.Nurbs import (
    basis_matrix,
    collapse_knots,
    expanded_surface_knots,
    greville_abscissae,
    interpolation_knots,
    solve_linear_system,
    surface_degrees,
    surface_domain,
    surface_normal,
)
from pyhopper.Utils.Planes import point_on_plane
from pyhopper.Utils.Vectors import distance


def plane_surface(plane: AtomicPlane, x_size: AtomicInterval, y_size: AtomicInterval) -> AtomicSurface:
    x0, x1 = float(x_size.start), float(x_size.end)
    y0, y1 = float(y_size.start), float(y_size.end)
    if x0 == x1 or y0 == y1:
        raise ValueError("Plane Surface needs non-empty size domains")
    poles = (
        (point_on_plane(plane, x0, y0), point_on_plane(plane, x1, y0)),
        (point_on_plane(plane, x0, y1), point_on_plane(plane, x1, y1)),
    )
    return AtomicSurface(
        poles=poles,
        weights=((1.0, 1.0), (1.0, 1.0)),
        u_knots=(min(x0, x1), max(x0, x1)),
        v_knots=(min(y0, y1), max(y0, y1)),
        u_mults=(2, 2),
        v_mults=(2, 2),
        u_degree=1,
        v_degree=1,
    )


def _curve_knot_data(curve: AtomicNurbsCurve) -> tuple[tuple[float, ...], tuple[int, ...]]:
    unique, mults = collapse_knots(curve.knots)
    return tuple(unique), tuple(mults)


def _weights(curve: AtomicNurbsCurve) -> tuple[float, ...]:
    if len(curve.weights) == len(curve.control_points):
        return tuple(float(w) for w in curve.weights)
    return tuple(1.0 for _ in curve.control_points)


def sum_surface(curve_a: AtomicNurbsCurve, curve_b: AtomicNurbsCurve) -> AtomicSurface:
    """Translational surface: curve A swept along curve B (B's start point pinned to A)."""
    if not curve_a.control_points or not curve_b.control_points:
        raise ValueError("Sum Surface needs two curves")
    start_b = curve_b.control_points[0]
    weights_a, weights_b = _weights(curve_a), _weights(curve_b)
    poles = tuple(
        tuple(AtomicPoint(a.x + b.x - start_b.x, a.y + b.y - start_b.y, a.z + b.z - start_b.z) for a in curve_a.control_points)
        for b in curve_b.control_points
    )
    weights = tuple(tuple(wa * wb for wa in weights_a) for wb in weights_b)
    u_knots, u_mults = _curve_knot_data(curve_a)
    v_knots, v_mults = _curve_knot_data(curve_b)
    return AtomicSurface(
        poles=poles,
        weights=weights,
        u_knots=u_knots,
        v_knots=v_knots,
        u_mults=u_mults,
        v_mults=v_mults,
        u_degree=int(curve_a.degree),
        v_degree=int(curve_b.degree),
    )


def extrude_to_point(curve: AtomicNurbsCurve, apex: AtomicPoint) -> AtomicSurface:
    """Ruled surface from every point of the curve to the apex (Grasshopper Extrude Point)."""
    if not curve.control_points:
        raise ValueError("Extrude Point needs a curve")
    reach = distance(curve.control_points[0], apex)
    if reach <= 1e-12:
        raise ValueError("Extrude Point needs an apex away from the curve start")
    weights = _weights(curve)
    poles = tuple((point, apex) for point in curve.control_points)
    v_knots, v_mults = _curve_knot_data(curve)
    return AtomicSurface(
        poles=poles,
        weights=tuple((w, w) for w in weights),
        u_knots=(0.0, reach),
        v_knots=v_knots,
        u_mults=(2, 2),
        v_mults=v_mults,
        u_degree=1,
        v_degree=int(curve.degree),
    )


def surface_control_points(surface: AtomicSurface) -> tuple[list[AtomicPoint], list[float], list[AtomicPoint], int, int]:
    """(points, weights, greville uv points, u count, v count), u outer and v inner like Grasshopper."""
    v_count = len(surface.poles)
    u_count = len(surface.poles[0]) if v_count else 0
    u_degree, v_degree = surface_degrees(surface)
    u_knots, v_knots = expanded_surface_knots(surface)
    u_greville = greville_abscissae(u_knots, u_degree, u_count)
    v_greville = greville_abscissae(v_knots, v_degree, v_count)
    points: list[AtomicPoint] = []
    weights: list[float] = []
    greville: list[AtomicPoint] = []
    for u in range(u_count):
        for v in range(v_count):
            points.append(surface.poles[v][u])
            weights.append(float(surface.weights[v][u]))
            greville.append(AtomicPoint(u_greville[u], v_greville[v], 0.0))
    return points, weights, greville, u_count, v_count


def surface_dimensions(surface: AtomicSurface) -> tuple[float, float]:
    """(u dimension, v dimension): the longest control-polygon length in each direction."""
    rows = surface.poles
    u_dimension = max((sum(distance(a, b) for a, b in zip(row, row[1:])) for row in rows), default=0.0)
    columns = list(zip(*rows)) if rows else []
    v_dimension = max((sum(distance(a, b) for a, b in zip(column, column[1:])) for column in columns), default=0.0)
    return u_dimension, v_dimension


def extrude_along(curve: AtomicNurbsCurve, direction: AtomicVector) -> AtomicSurface:
    """Ruled surface sweeping the curve along ``direction``.

    Grasshopper's Extrude Linear layout: U runs along the extrusion with the
    domain ``[0, |direction|]``, V follows the profile's own knots.
    """
    reach = math.sqrt(direction.x ** 2 + direction.y ** 2 + direction.z ** 2)
    if reach <= 1e-12:
        raise ValueError("Extrusion needs a non-zero direction")
    weights = _weights(curve)
    poles = tuple((point, AtomicPoint(point.x + direction.x, point.y + direction.y, point.z + direction.z)) for point in curve.control_points)
    v_knots, v_mults = _curve_knot_data(curve)
    return AtomicSurface(
        poles=poles,
        weights=tuple((w, w) for w in weights),
        u_knots=(0.0, reach),
        v_knots=v_knots,
        u_mults=(2, 2),
        v_mults=v_mults,
        u_degree=1,
        v_degree=int(curve.degree),
    )


def control_point_loft(curves: Sequence[AtomicNurbsCurve], degree: int) -> AtomicSurface:
    """Surface whose pole rows are the curves' control points (Grasshopper Control Point Loft).

    All curves need the same control-point count and degree; V is a clamped
    uniform B-spline of ``min(degree, count - 1)`` through the rows.
    """
    if len(curves) < 2:
        raise ValueError("Control Point Loft needs at least two curves")
    reference = curves[0]
    for curve in curves[1:]:
        if len(curve.control_points) != len(reference.control_points) or int(curve.degree) != int(reference.degree):
            raise ValueError("Control Point Loft needs curves with matching control-point counts and degrees")
    v_degree = max(1, min(int(degree), len(curves) - 1))
    u_knots, u_mults = _curve_knot_data(reference)
    v_knots, v_mults = _uniform_clamped(len(curves), v_degree)
    return AtomicSurface(
        poles=tuple(tuple(curve.control_points) for curve in curves),
        weights=tuple(_weights(curve) for curve in curves),
        u_knots=u_knots,
        v_knots=v_knots,
        u_mults=u_mults,
        v_mults=v_mults,
        u_degree=int(reference.degree),
        v_degree=v_degree,
    )


def _uniform_clamped(count: int, degree: int) -> tuple[tuple[float, ...], tuple[int, ...]]:
    """Clamped uniform knots on [0, 1] as (unique knots, multiplicities)."""
    spans = count - degree
    if spans <= 1:
        return (0.0, 1.0), (degree + 1, degree + 1)
    return tuple(k / spans for k in range(spans + 1)), (degree + 1,) + (1,) * (spans - 1) + (degree + 1,)


def _averaged_parameters(rows: Sequence[Sequence[AtomicPoint]]) -> list[float]:
    """Chord-length parameters averaged over the rows (The NURBS Book, 9.2.5)."""
    count = len(rows[0])
    totals = [0.0] * count
    for row in rows:
        lengths = [distance(row[k - 1], row[k]) for k in range(1, count)]
        total = sum(lengths) or 1.0
        running = 0.0
        for k in range(1, count):
            running += lengths[k - 1]
            totals[k] += running
    return [value / len(rows) for value in totals]


def surface_from_grid(grid: Sequence[Sequence[AtomicPoint]], interpolate: bool) -> AtomicSurface:
    """Surface over ``grid[v][u]``: a control-point surface, or one interpolating the points.

    Degrees are ``min(3, count - 1)`` per direction with clamped knots on [0, 1]
    for control points; interpolation uses averaged chord-length parameters and
    averaged knots (Grasshopper's Surface From Points).
    """
    v_count, u_count = len(grid), len(grid[0])
    u_degree, v_degree = min(3, u_count - 1), min(3, v_count - 1)
    if u_degree < 1 or v_degree < 1:
        raise ValueError("A surface needs at least two points in each direction")
    if not interpolate:
        u_knots, u_mults = _uniform_clamped(u_count, u_degree)
        v_knots, v_mults = _uniform_clamped(v_count, v_degree)
        return AtomicSurface(poles=tuple(tuple(row) for row in grid), u_knots=u_knots, v_knots=v_knots, u_mults=u_mults, v_mults=v_mults, u_degree=u_degree, v_degree=v_degree)
    u_parameters = _averaged_parameters(grid)
    v_parameters = _averaged_parameters([[grid[v][u] for v in range(v_count)] for u in range(u_count)])
    full_u = interpolation_knots(u_parameters, u_degree)
    full_v = interpolation_knots(v_parameters, v_degree)
    # interpolate every row along U, then the resulting columns along V
    u_matrix = basis_matrix(u_parameters, full_u, u_degree)
    rows = [solve_linear_system(u_matrix, [[p.x, p.y, p.z] for p in row], "Surface From Points could not interpolate") for row in grid]
    v_matrix = basis_matrix(v_parameters, full_v, v_degree)
    poles = [[None] * u_count for _ in range(v_count)]
    for u in range(u_count):
        column = solve_linear_system(v_matrix, [rows[v][u] for v in range(v_count)], "Surface From Points could not interpolate")
        for v in range(v_count):
            poles[v][u] = AtomicPoint(*column[v])
    u_knots, u_mults = collapse_knots(full_u)
    v_knots, v_mults = collapse_knots(full_v)
    return AtomicSurface(poles=tuple(tuple(row) for row in poles), u_knots=u_knots, v_knots=v_knots, u_mults=u_mults, v_mults=v_mults, u_degree=u_degree, v_degree=v_degree)


def rectangle_corners(rectangle) -> list[AtomicPoint]:
    """The five vertices (closed loop) of a centred rectangle, counter-clockwise from (x-, y-)."""
    half_x, half_y = float(rectangle.x_size) / 2.0, float(rectangle.y_size) / 2.0
    corners = [point_on_plane(rectangle.plane, sx * half_x, sy * half_y) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return corners + [corners[0]]


def flip_surface(surface: AtomicSurface) -> AtomicSurface:
    """The same surface with U and V swapped, which reverses its normal."""
    v_count, u_count = len(surface.poles), len(surface.poles[0])
    return AtomicSurface(
        poles=tuple(tuple(surface.poles[v][u] for v in range(v_count)) for u in range(u_count)),
        weights=tuple(tuple(surface.weights[v][u] for v in range(v_count)) for u in range(u_count)),
        u_knots=surface.v_knots,
        v_knots=surface.u_knots,
        u_mults=surface.v_mults,
        v_mults=surface.u_mults,
        u_degree=surface.v_degree,
        v_degree=surface.u_degree,
        u_periodic=surface.v_periodic,
        v_periodic=surface.u_periodic,
    )


def surface_normal_at_centre(surface: AtomicSurface) -> AtomicVector:
    """Unit normal at the middle of the surface's domain."""
    (u0, u1), (v0, v1) = surface_domain(surface)
    return surface_normal(surface, 0.5 * (u0 + u1), 0.5 * (v0 + v1))
