"""ClosestPoints - Find closest points in a point collection (Grasshopper "Closest Points")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Points import nearest_indices


class ClosestPoints(Component):
    """Find closest points in a point collection.

    Inputs:
        point: Point to search from (Grasshopper Point [item]).
        cloud: Cloud of points to search (Grasshopper Cloud [list]).
        count: Number of closest points to find (Grasshopper Count [item]).

    Outputs:
        closest_point: Point in [C] closest to [P] (Grasshopper Closest Point).
        cp_index: Index of closest point (Grasshopper CP Index).
        distance: Distance between [P] and [C](i) (Grasshopper Distance).

    Notes:
        Grasshopper: Vector > Point > Closest Points (CPs).
        pyhopper decisions: results are ordered nearest first, ties by lowest index; ``count`` is capped at the
        cloud size; Grasshopper default ``count = 3``.
    """

    display_name = "Closest Points"
    nickname = "CPs"
    gh_guid = "446014c4-c11c-45a7-8839-c45dc60950d6"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("cloud", AtomicPoint, Access.LIST),
        InputParam("count", int, Access.ITEM, default=3),
    ]
    outputs = [
        OutputParam("closest_point", AtomicPoint, access=Access.LIST),
        OutputParam("cp_index", int, access=Access.LIST),
        OutputParam("distance", float, access=Access.LIST),
    ]

    def generate(self, point=AtomicPoint.origin(), cloud=None, count=3):
        candidates = list(cloud or [])
        found = nearest_indices(point, candidates, max(0, int(count)))
        return [candidates[index] for index, _ in found], [index for index, _ in found], [gap for _, gap in found]
