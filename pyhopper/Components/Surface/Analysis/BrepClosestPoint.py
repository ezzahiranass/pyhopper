"""BrepClosestPoint - Find the closest point on a brep (Grasshopper "Brep Closest Point")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBrep, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import brep_closest_point


class BrepClosestPoint(Component):
    """Find the closest point on a brep.

    Inputs:
        point: Sample point (Grasshopper Point [item]).
        brep: Base Brep (Grasshopper Brep [item]).

    Outputs:
        point: Closest point (Grasshopper Point).
        normal: Normal direction at closest point (Grasshopper Normal).
        distance: Distance between sample point and Brep (Grasshopper Distance).

    Notes:
        Grasshopper: Surface > Analysis > Brep Closest Point (Brep CP).
        pyhopper decisions: Grasshopper-verified — the closest point over the brep's faces (untrimmed
        in pyhopper), the unit surface normal there and the distance; surfaces and boxes coerce to
        breps.
    """

    display_name = "Brep Closest Point"
    nickname = "Brep CP"
    gh_guid = "4beead95-8aa2-4613-8bb9-24758a0f5c4c"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("brep", AtomicBrep, Access.ITEM),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("normal", AtomicVector),
        OutputParam("distance", float),
    ]

    def generate(self, point=AtomicPoint.origin(), brep=None):
        return brep_closest_point(brep, point)
