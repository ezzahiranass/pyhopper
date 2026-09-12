"""SortPoints - Sort points by Euclidean coordinates (first x, then y, then z) (Grasshopper "Sort Points")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Points import sort_points


class SortPoints(Component):
    """Sort points by Euclidean coordinates (first x, then y, then z).

    Inputs:
        points: Points to sort (Grasshopper Points [list]).

    Outputs:
        points: Sorted points (Grasshopper Points).
        indices: Point index map (Grasshopper Indices).

    Notes:
        Grasshopper: Vector > Point > Sort Points (Sort Pt).
        pyhopper decisions: sorts by x, then y, then z with a stable sort (coincident points keep their order),
        like Grasshopper.
    """

    display_name = "Sort Points"
    nickname = "Sort Pt"
    gh_guid = "4e86ba36-05e2-4cc0-a0f5-3ad57c91f04e"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("indices", int, access=Access.LIST),
    ]

    def generate(self, points=None):
        return sort_points(list(points or []))
