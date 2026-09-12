"""SortAlongCurve - Sort points along a curve (Grasshopper "Sort Along Curve")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import curve_closest_point
from pyhopper.Core.TypeSystem import CURVE


class SortAlongCurve(Component):
    """Sort points along a curve.

    Inputs:
        points: Points to sort (Grasshopper Points [list]).
        curve: Curve to sort along (Grasshopper Curve [item]).

    Outputs:
        points: Sorted points (Grasshopper Points).
        indices: Point index map (Grasshopper Indices).

    Notes:
        Grasshopper: Vector > Point > Sort Along Curve (AlongCrv).
        pyhopper decisions: Grasshopper-verified — points sorted by the parameter of their closest
        point on the curve (stable for ties), with their original indices.
    """

    display_name = "Sort Along Curve"
    nickname = "AlongCrv"
    gh_guid = "59aaebf8-6654-46b7-8386-89223c773978"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
        InputParam("curve", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("indices", int, access=Access.LIST),
    ]

    def generate(self, points=None, curve=None):
        items = list(points or [])
        order = sorted(range(len(items)), key=lambda index: curve_closest_point(curve, items[index])[0])
        return [items[index] for index in order], order
