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

from pyhopper.Core.Atoms import AtomicInterval, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicSurface
from pyhopper.Utils.Nurbs import collapse_knots, expanded_surface_knots, greville_abscissae, surface_degrees
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
