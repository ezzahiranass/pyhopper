"""DeconstructPlane - Deconstruct a plane into its component parts (Grasshopper "Deconstruct Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DeconstructPlane(Component):
    """Deconstruct a plane into its component parts.

    Inputs:
        plane: Plane to deconstruct (Grasshopper Plane [item]).

    Outputs:
        origin: Origin point (Grasshopper Origin).
        x_axis: X-Axis vector (Grasshopper X-Axis).
        y_axis: Y-Axis vector (Grasshopper Y-Axis).
        z_axis: Z-Axis vector (Grasshopper Z-Axis).

    Notes:
        Grasshopper: Vector > Plane > Deconstruct Plane (DePlane).
        pyhopper decisions: none; behaviour matches Grasshopper.
    """

    display_name = "Deconstruct Plane"
    nickname = "DePlane"
    gh_guid = "3cd2949b-4ea8-4ffb-a70c-5c380f9f46ea"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("origin", AtomicPoint),
        OutputParam("x_axis", AtomicVector),
        OutputParam("y_axis", AtomicVector),
        OutputParam("z_axis", AtomicVector),
    ]

    def generate(self, plane=AtomicPlane.world_xy()):
        return plane.origin, plane.x_axis, plane.y_axis, plane.normal
