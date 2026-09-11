"""DivideCurve - Divide a curve into equal-length segments (Grasshopper "Divide Curve")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicNurbsCurve, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Curves import divide_nurbs_curve_by_count, is_closed_nurbs_curve, nurbs_curve_domain
from pyhopper.Utils.Nurbs import collapse_knots
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


def _kink_parameters(curve: AtomicNurbsCurve) -> list[float]:
    """Interior parameters where the curve is only positionally continuous (knot multiplicity >= degree)."""
    start, end = nurbs_curve_domain(curve)
    unique, mults = collapse_knots(curve.knots)
    return [knot for knot, mult in zip(unique, mults) if start < knot < end and mult >= curve.degree]


def _sub_curve(curve: AtomicNurbsCurve, start: float, end: float) -> AtomicNurbsCurve:
    """Restrict a curve to [start, end] between two C0 knots (no geometry change).

    Both bounds are knots of multiplicity >= degree (or the domain ends), so the
    piece is itself a clamped B-spline: its control points are the consecutive
    slice starting ``degree`` positions before the last occurrence of ``start``.
    """
    degree = curve.degree
    knots = curve.knots
    last_start_index = max(index for index, knot in enumerate(knots) if knot == start)
    interior = tuple(knot for knot in knots if start < knot < end)
    new_knots = (start,) * (degree + 1) + interior + (end,) * (degree + 1)
    control_start = last_start_index - degree
    control_count = len(new_knots) - degree - 1
    control_points = curve.control_points[control_start : control_start + control_count]
    weights = (
        curve.weights[control_start : control_start + control_count]
        if len(curve.weights) == len(curve.control_points)
        else tuple(1.0 for _ in control_points)
    )
    return AtomicNurbsCurve(control_points=control_points, weights=weights, knots=new_knots, degree=degree)


class DivideCurve(Component):
    """Divide a curve into ``count`` segments of equal arc length.

    Returns the division points, the unit tangents and the curve parameters at
    those points. Open curves yield ``count + 1`` points, closed curves
    ``count`` (the seam is not repeated). With ``kinks`` enabled the curve is
    first split at its kinks (polyline vertices, C0 knots) and every piece is
    divided into ``count`` segments.

    Notes:
        Grasshopper: Curve > Division > Divide Curve (Divide).
        pyhopper decisions: division is by arc length measured on the unified
        NURBS curve (tolerance 1e-7); parameters are in the native curve domain.
    """

    display_name = "Divide Curve"
    nickname = "Divide"
    gh_guid = "2162e72e-72fc-4bf8-9459-d4d82fa8aa14"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("count", int, Access.ITEM, default=10),
        InputParam("kinks", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("tangents", AtomicVector, access=Access.LIST),
        OutputParam("parameters", float, access=Access.LIST),
    ]

    def generate(self, curve=None, count=10, kinks=False):
        nurbs = as_nurbs_curve(curve)
        segments = int(count)
        if segments < 1:
            raise ValueError("DivideCurve requires a positive segment count")

        breaks = _kink_parameters(nurbs) if kinks else []
        if not breaks:
            return divide_nurbs_curve_by_count(nurbs, segments)

        start, end = nurbs_curve_domain(nurbs)
        closed = is_closed_nurbs_curve(nurbs)
        points: list[AtomicPoint] = []
        tangents: list[AtomicVector] = []
        parameters: list[float] = []
        bounds = [start, *breaks, end]
        for index, (piece_start, piece_end) in enumerate(zip(bounds, bounds[1:])):
            piece = _sub_curve(nurbs, piece_start, piece_end)
            piece_points, piece_tangents, piece_parameters = divide_nurbs_curve_by_count(piece, segments)
            if index > 0:  # the shared kink point was already emitted by the previous piece
                piece_points, piece_tangents, piece_parameters = piece_points[1:], piece_tangents[1:], piece_parameters[1:]
            points.extend(piece_points)
            tangents.extend(piece_tangents)
            parameters.extend(piece_parameters)
        if closed and len(points) > 1:
            points, tangents, parameters = points[:-1], tangents[:-1], parameters[:-1]
        return points, tangents, parameters
