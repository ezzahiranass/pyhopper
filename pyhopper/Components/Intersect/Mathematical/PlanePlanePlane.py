"""PlanePlanePlane - Solve the intersection events of three planes (Grasshopper "Plane | Plane | Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._closed_form import line_plane_intersection, plane_plane_intersection


class PlanePlanePlane(Component):
    """Solve the intersection events of three planes.

    Inputs:
        plane_a: First plane (Grasshopper Plane A [item]).
        plane_b: Second plane (Grasshopper Plane B [item]).
        plane_c: Third plane (Grasshopper Plane C [item]).

    Outputs:
        point: Intersection point (Grasshopper Point).
        line_ab: Intersection line between A and B (Grasshopper Line AB).
        line_ac: Intersection line between A and C (Grasshopper Line AC).
        line_bc: Intersection line between B and C (Grasshopper Line BC).

    Notes:
        Grasshopper: Intersect > Mathematical > Plane | Plane | Plane (3PX).
        pyhopper decisions: the three pairwise lines follow Plane | Plane (a line from the projected
        origins' midpoint along ``nB × nA`` at the cross product's own length); parallel pairs emit nothing for their line and for the
        point, as Grasshopper leaves them null.
    """

    display_name = "Plane | Plane | Plane"
    nickname = "3PX"
    gh_guid = "f1ea5a4b-1a4f-4cf4-ad94-1ecfb9302b6e"

    inputs = [
        InputParam("plane_a", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("plane_b", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("plane_c", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("line_ab", AtomicLine),
        OutputParam("line_ac", AtomicLine),
        OutputParam("line_bc", AtomicLine),
    ]

    def generate(self, plane_a=AtomicPlane.world_xy(), plane_b=AtomicPlane.world_xy(), plane_c=AtomicPlane.world_xy()):
        line_ab = plane_plane_intersection(plane_a, plane_b)
        line_ac = plane_plane_intersection(plane_a, plane_c)
        line_bc = plane_plane_intersection(plane_b, plane_c)
        point = Component.NO_OUTPUT
        if line_ab is not None:
            hit = line_plane_intersection(line_ab, plane_c)
            if hit is not None:
                point = hit[0]
        return (
            point,
            Component.NO_OUTPUT if line_ab is None else line_ab,
            Component.NO_OUTPUT if line_ac is None else line_ac,
            Component.NO_OUTPUT if line_bc is None else line_bc,
        )
