"""Extrude - Extrude a base shape along a direction vector."""

from __future__ import annotations

from pyhopper.Core.Atoms import (
    AtomicBrep,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPoint,
    AtomicSurface,
    AtomicVector,
)
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


def _collapse_repeated_knots(knots: tuple[float, ...]) -> tuple[tuple[float, ...], tuple[int, ...]]:
    if not knots:
        return (), ()

    unique_knots = [knots[0]]
    multiplicities = [1]

    for knot in knots[1:]:
        if knot == unique_knots[-1]:
            multiplicities[-1] += 1
        else:
            unique_knots.append(knot)
            multiplicities.append(1)

    return tuple(unique_knots), tuple(multiplicities)


def _nurbs_profile(curve: AtomicNurbsCurve) -> tuple[
    tuple[AtomicPoint, ...],
    tuple[float, ...],
    tuple[float, ...],
    tuple[int, ...],
    int,
]:
    """Extract surface-ready pole/weight/knot data from a NURBS curve.

    Returns (poles, weights, unique_knots, mults, degree).
    """
    from pyhopper.Core.Atoms import _open_uniform_bspline_data

    if len(curve.control_points) < 2:
        raise ValueError("Extrude requires curves with at least two control points")

    degree = max(1, min(int(curve.degree), len(curve.control_points) - 1))
    weights = (
        curve.weights
        if len(curve.weights) == len(curve.control_points)
        else tuple(1.0 for _ in curve.control_points)
    )

    if not curve.knots:
        knots, mults, degree = _open_uniform_bspline_data(len(curve.control_points), degree)
    else:
        raw_knots = tuple(float(k) for k in curve.knots)
        expected_full = len(curve.control_points) + degree + 1
        expected_unique = len(curve.control_points) - degree + 1

        if len(raw_knots) == expected_full:
            knots, mults = _collapse_repeated_knots(raw_knots)
        elif len(raw_knots) == expected_unique:
            knots = raw_knots
            mults = tuple(
                degree + 1 if i in (0, len(raw_knots) - 1) else 1
                for i in range(len(raw_knots))
            )
        else:
            raise ValueError(
                "Extrude could not interpret the NURBS knot vector"
            )

    return curve.control_points, weights, knots, mults, degree


def _translate_point(p: AtomicPoint, v: AtomicVector) -> AtomicPoint:
    return AtomicPoint(p.x + v.x, p.y + v.y, p.z + v.z)


def _make_wall(poles, weights, knots, mults, degree, direction):
    """Build a ruled wall surface by translating a boundary curve."""
    translated = tuple(_translate_point(p, direction) for p in poles)
    return AtomicSurface(
        poles=(poles, translated),
        weights=(weights, weights),
        u_knots=knots,
        v_knots=(0.0, 1.0),
        u_mults=mults,
        v_mults=(2, 2),
        u_degree=degree,
        v_degree=1,
    )


def _extrude_point(point: AtomicPoint, direction: AtomicVector) -> AtomicLine:
    return AtomicLine(start=point, end=_translate_point(point, direction))


def _extrude_curve(curve: AtomicNurbsCurve, direction: AtomicVector) -> AtomicSurface:
    poles, weights, knots, mults, degree = _nurbs_profile(curve)
    return _make_wall(poles, weights, knots, mults, degree, direction)


def _extrude_surface(surface: AtomicSurface, direction: AtomicVector) -> AtomicBrep:
    """Extrude a surface into a closed Brep with 6 faces.

    For a clamped tensor-product B-spline, the four boundary iso-curves
    are exactly the edge rows and columns of the pole grid — no
    approximation or evaluation needed.
    """
    v_count = len(surface.poles)

    # Top cap: translate all poles
    translated_poles = tuple(
        tuple(_translate_point(p, direction) for p in row)
        for row in surface.poles
    )
    top_cap = AtomicSurface(
        poles=translated_poles,
        weights=surface.weights,
        u_knots=surface.u_knots,
        v_knots=surface.v_knots,
        u_mults=surface.u_mults,
        v_mults=surface.v_mults,
        u_degree=surface.u_degree,
        v_degree=surface.v_degree,
        u_periodic=surface.u_periodic,
        v_periodic=surface.v_periodic,
    )

    # Four boundary curves → four ruled wall surfaces
    # v_min edge (first row, runs in u)
    wall_v0 = _make_wall(
        surface.poles[0], surface.weights[0],
        surface.u_knots, surface.u_mults, surface.u_degree, direction,
    )
    # v_max edge (last row, runs in u)
    wall_v1 = _make_wall(
        surface.poles[-1], surface.weights[-1],
        surface.u_knots, surface.u_mults, surface.u_degree, direction,
    )
    # u_min edge (first column, runs in v)
    u0_poles = tuple(surface.poles[i][0] for i in range(v_count))
    u0_weights = tuple(surface.weights[i][0] for i in range(v_count))
    wall_u0 = _make_wall(
        u0_poles, u0_weights,
        surface.v_knots, surface.v_mults, surface.v_degree, direction,
    )
    # u_max edge (last column, runs in v)
    u1_poles = tuple(surface.poles[i][-1] for i in range(v_count))
    u1_weights = tuple(surface.weights[i][-1] for i in range(v_count))
    wall_u1 = _make_wall(
        u1_poles, u1_weights,
        surface.v_knots, surface.v_mults, surface.v_degree, direction,
    )

    return AtomicBrep(faces=(surface, top_cap, wall_v0, wall_v1, wall_u0, wall_u1))


class Extrude(Component):
    """Extrude a base shape along a direction vector.

    Accepts a point, any supported curve type, or a surface. Points extrude
    into lines; curves extrude into surfaces; surfaces extrude into a list
    of six boundary surfaces (bottom cap, top cap, and four side walls)
    that together form a closed solid shell.
    """

    inputs = [
        InputParam("base", None, Access.ITEM),
        InputParam("direction", AtomicVector, Access.ITEM, default=AtomicVector(0.0, 0.0, 1.0)),
    ]
    outputs = [OutputParam("extrusion")]

    def generate(self, base=None, direction=AtomicVector(0.0, 0.0, 1.0)):
        if isinstance(base, AtomicPoint):
            return _extrude_point(base, direction)

        if isinstance(base, AtomicSurface):
            return _extrude_surface(base, direction)

        return _extrude_curve(as_nurbs_curve(base), direction)
