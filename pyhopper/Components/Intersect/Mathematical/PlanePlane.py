"""PlanePlane - Solve the intersection event of two planes (Grasshopper "Plane | Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._closed_form import plane_plane_intersection


class PlanePlane(Component):
    """Solve the intersection event of two planes.

    Inputs:
        plane_a: First plane (Grasshopper Plane A [item]).
        plane_b: Second plane (Grasshopper Plane B [item]).

    Outputs:
        line: Intersection line (Grasshopper Line).

    Notes:
        Grasshopper: Intersect > Mathematical > Plane | Plane (PPX).
        pyhopper decisions: a unit-length line starting at the projection of the two origins' midpoint onto the
        intersection, running along ``normal_b x normal_a`` — Grasshopper's exact answer; parallel
        planes emit nothing.
    """

    display_name = "Plane | Plane"
    nickname = "PPX"
    gh_guid = "290cf9c4-0711-4704-851e-4c99e3343ac5"

    inputs = [
        InputParam("plane_a", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("plane_b", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("line", AtomicLine),
    ]

    def generate(self, plane_a=AtomicPlane.world_xy(), plane_b=AtomicPlane.world_xy()):
        line = plane_plane_intersection(plane_a, plane_b)
        return Component.NO_OUTPUT if line is None else line
