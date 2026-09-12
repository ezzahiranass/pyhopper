"""PullPoint - Pull a point to a variety of geometry (Grasshopper "Pull Point")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import geometry_closest_point
from pyhopper.Core.TypeSystem import GEOMETRY


class PullPoint(Component):
    """Pull a point to a variety of geometry.

    Inputs:
        point: Point to search from (Grasshopper Point [item]).
        geometry: Geometry that pulls (Grasshopper Geometry [list]).

    Outputs:
        closest_point: Point on [G] closest to [P] (Grasshopper Closest Point).
        distance: Distance between [P] and its projection onto [G] (Grasshopper Distance).
        index: Index on [G] (Grasshopper Index).

    Notes:
        Grasshopper: Vector > Point > Pull Point (Pull).
        pyhopper decisions: Grasshopper-verified — the closest point over all geometry items (points,
        curves, planes, surfaces, breps and boxes), its distance and the index of the item; ties go to
        the first item. An empty geometry list emits nothing.
    """

    display_name = "Pull Point"
    nickname = "Pull"
    gh_guid = "902289da-28dc-454b-98d4-b8f8aa234516"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("geometry", GEOMETRY, Access.LIST),
    ]
    outputs = [
        OutputParam("closest_point", AtomicPoint),
        OutputParam("distance", float),
        OutputParam("index", int),
    ]

    def generate(self, point=AtomicPoint.origin(), geometry=None):
        best = None
        for index, item in enumerate(geometry or []):
            closest, d = geometry_closest_point(item, point)
            if best is None or d < best[1] - 1e-12:
                best = (closest, d, index)
        if best is None:
            return Component.NO_OUTPUT, Component.NO_OUTPUT, Component.NO_OUTPUT
        return best
