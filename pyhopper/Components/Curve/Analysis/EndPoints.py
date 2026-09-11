"""EndPoints - Extract the end points of a curve (Grasshopper "End Points")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_start_end
from pyhopper.Core.TypeSystem import CURVE


class EndPoints(Component):
    """Extract the end points of a curve.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).

    Outputs:
        start: Curve start point (Grasshopper Start).
        end: Curve end point (Grasshopper End).

    Notes:
        Grasshopper: Curve > Analysis > End Points (End).
        pyhopper decisions: none; behaviour matches Grasshopper (a closed curve reports its seam twice).
    """

    display_name = "End Points"
    nickname = "End"
    gh_guid = "11bbd48b-bb0a-4f1b-8167-fa297590390d"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("start", AtomicPoint),
        OutputParam("end", AtomicPoint),
    ]

    def generate(self, curve=None):
        return curve_start_end(curve)
