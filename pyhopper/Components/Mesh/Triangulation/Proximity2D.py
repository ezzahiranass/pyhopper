"""Proximity2D - Search for two-dimensional proximity within a point list (Grasshopper "Proximity 2D")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicLine
from pyhopper.Utils.Hull import proximity_links


class Proximity2D(Component):
    """Search for two-dimensional proximity within a point list.

    Inputs:
        points: Input points (Grasshopper Points [list]).
        plane: Optional base plane. If null, the best fit plane is used (Grasshopper Plane [item]).
        group: Maximum number of closest points to find (Grasshopper Group [item]).
        min_radius: Optional minimum search radius. (Grasshopper Min Radius [item]).
        max_radius: Optional maximum search radius. (Grasshopper Max Radius [item]).

    Outputs:
        links: Proximity links (Grasshopper Links).
        topology: Proximity topology (Grasshopper Topology).

    Notes:
        Grasshopper: Mesh > Triangulation > Proximity 2D (Prox).
        pyhopper decisions: every point links to its ``group`` nearest other points within the radius
        range (closest first, equal distances higher index first — Grasshopper-verified), one branch per
        point at ``{path;point}`` for both the link lines and the neighbour indices; a point with no
        neighbours keeps an empty branch. Default group 5.
        Distances are measured in the plane (world XY by default), so elevation is ignored.
    """

    display_name = "Proximity 2D"
    nickname = "Prox"
    gh_guid = "458ed0e0-19a3-419b-8ead-f524925b8a35"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("group", int, Access.ITEM, default=5),
        InputParam("min_radius", float, Access.ITEM, optional=True),
        InputParam("max_radius", float, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("links", AtomicLine, access=Access.TREE),
        OutputParam("topology", int, access=Access.TREE),
    ]

    def generate(self, points=None, plane=AtomicPlane.world_xy(), group=5, min_radius=None, max_radius=None):
        cloud = list(points or [])
        links = proximity_links(cloud, int(group), None if min_radius is None else float(min_radius), None if max_radius is None else float(max_radius), plane)
        lines = [[AtomicLine(cloud[index], cloud[other]) for other in neighbours] for index, neighbours in enumerate(links)]
        return self.sub_branches(lines, iteration=False), self.sub_branches(links, iteration=False)
