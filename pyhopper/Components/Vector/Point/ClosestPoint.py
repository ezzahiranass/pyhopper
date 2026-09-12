"""ClosestPoint - Find closest point in a point collection (Grasshopper "Closest Point")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Points import nearest_indices


class ClosestPoint(Component):
    """Find closest point in a point collection.

    Inputs:
        point: Point to search from (Grasshopper Point [item]).
        cloud: Cloud of points to search (Grasshopper Cloud [list]).

    Outputs:
        closest_point: Point in [C] closest to [P] (Grasshopper Closest Point).
        cp_index: Index of closest point (Grasshopper CP Index).
        distance: Distance between [P] and [C](i) (Grasshopper Distance).

    Notes:
        Grasshopper: Vector > Point > Closest Point (CP).
        pyhopper decisions: ties go to the lowest cloud index, like Grasshopper; an empty cloud emits nothing
        (Grasshopper emits nulls).
    """

    display_name = "Closest Point"
    nickname = "CP"
    gh_guid = "571ca323-6e55-425a-bf9e-ee103c7ba4b9"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("cloud", AtomicPoint, Access.LIST),
    ]
    outputs = [
        OutputParam("closest_point", AtomicPoint),
        OutputParam("cp_index", int),
        OutputParam("distance", float),
    ]

    def generate(self, point=AtomicPoint.origin(), cloud=None):
        candidates = list(cloud or [])
        if not candidates:
            return Component.NO_OUTPUT, Component.NO_OUTPUT, Component.NO_OUTPUT
        index, gap = nearest_indices(point, candidates, 1)[0]
        return candidates[index], index, gap
