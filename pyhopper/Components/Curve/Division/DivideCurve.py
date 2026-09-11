"""DivideCurve - Divide a curve into equal-length segments (Grasshopper "Divide Curve")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicNurbsCurve, AtomicPoint, AtomicPolyline, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Curves import curve_domain_of, divide_curve_by_count, sample_curve
from pyhopper.Utils.Nurbs import collapse_knots

_TOLERANCE = 1e-9


def kink_parameters(curve) -> list[float]:
    """Interior parameters where the curve is only positionally continuous.

    Polyline vertices, and NURBS knots of multiplicity >= degree; smooth atoms
    (lines, arcs, circles) have none.
    """
    if isinstance(curve, AtomicPolyline):
        count = len(curve.points) - 1
        return [index / count for index in range(1, count)]
    if isinstance(curve, AtomicNurbsCurve):
        start, end = curve_domain_of(curve)
        unique, mults = collapse_knots(curve.knots)
        return [knot for knot, mult in zip(unique, mults) if start < knot < end and mult >= curve.degree]
    return []


class DivideCurve(Component):
    """Divide a curve into ``count`` segments of equal arc length.

    Returns the division points, the unit tangents and the curve parameters at
    those points. Open curves yield ``count + 1`` points, closed curves
    ``count`` (the seam is not repeated). With ``kinks`` enabled the kink
    points (polyline vertices, C0 knots) are added to the division points.

    Notes:
        Grasshopper: Curve > Division > Divide Curve (Divide).
        pyhopper decisions: division is by arc length (tolerance 1e-7);
        parameters follow each curve kind's Grasshopper parameterisation on
        [0, 1] (lines by length, polylines per segment, arcs by angle) and the
        knot domain for NURBS, so they match a reparameterised Grasshopper curve;
        ``kinks`` inserts the kink parameters among the regular divisions, exactly
        like Grasshopper (it does not divide every segment separately).
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
        segments = int(count)
        if segments < 1:
            raise ValueError("DivideCurve requires a positive segment count")
        points, tangents, parameters = divide_curve_by_count(curve, segments)
        if not kinks:
            return points, tangents, parameters
        merged = list(parameters)
        start, end = curve_domain_of(curve)
        scale = max(1.0, abs(end - start))
        for kink in kink_parameters(curve):
            if all(abs(kink - existing) > _TOLERANCE * scale for existing in merged):
                merged.append(kink)
        merged.sort()
        return sample_curve(curve, merged)
