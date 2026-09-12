"""CurveProximity - Find the pair of closest points between two curves (Grasshopper "Curve Proximity")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import curve_curve_closest
from pyhopper.Core.TypeSystem import CURVE


class CurveProximity(Component):
    """Find the pair of closest points between two curves.

    Inputs:
        curve_a: First curve (Grasshopper Curve A [item]).
        curve_b: Second curve (Grasshopper Curve B [item]).

    Outputs:
        point_a: Point on curve A closest to curve B (Grasshopper Point A).
        point_b: Point on curve B closest to curve A (Grasshopper Point B).
        distance: Smallest distance between two curves (Grasshopper Distance).

    Notes:
        Grasshopper: Curve > Analysis > Curve Proximity (CrvProx).
        pyhopper decisions: Grasshopper-verified — the closest pair of points between the two curves
        (best sampled pair refined by alternating closest-point projections); parallel stretches pick
        the earliest pair, where Rhino's choice is arbitrary.
    """

    display_name = "Curve Proximity"
    nickname = "CrvProx"
    gh_guid = "6b7ba278-5c9d-42f1-a61d-6209cbd44907"

    inputs = [
        InputParam("curve_a", CURVE, Access.ITEM),
        InputParam("curve_b", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("point_a", AtomicPoint),
        OutputParam("point_b", AtomicPoint),
        OutputParam("distance", float),
    ]

    def generate(self, curve_a=None, curve_b=None):
        _, _, point_a, point_b, d = curve_curve_closest(curve_a, curve_b)
        return point_a, point_b, d
