"""PointGroups - Create groups from nearby points (Grasshopper "Point Groups")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Points import group_by_distance


class PointGroups(Component):
    """Create groups from nearby points.

    Inputs:
        points: Points to group (Grasshopper Points [list]).
        distance: Distance threshold for group inclusion (Grasshopper Distance [item]).

    Outputs:
        groups: Point groups (Grasshopper Groups).
        indices: Group indices (Grasshopper Indices).

    Notes:
        Grasshopper: Vector > Point > Point Groups (PGroups).
        pyhopper decisions: points linked by chains of neighbours at most ``distance`` apart form
        one group (distance 0 groups coincident points); groups and indices come out in
        Grasshopper's order — groups by their highest index, members from the highest index down —
        one branch per group at ``{path;group}`` (Grasshopper appends only the group
        index, so several distance values in one branch share the same group paths).
    """

    display_name = "Point Groups"
    nickname = "PGroups"
    gh_guid = "81f6afc9-22d9-49f0-8579-1fd7e0df6fa6"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
        InputParam("distance", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("groups", AtomicPoint, access=Access.TREE),
        OutputParam("indices", int, access=Access.TREE),
    ]

    def generate(self, points=None, distance=1.0):
        cloud = list(points or [])
        groups = group_by_distance(cloud, float(distance))
        return self.sub_branches([[cloud[index] for index in group] for group in groups], iteration=False), self.sub_branches(groups, iteration=False)
