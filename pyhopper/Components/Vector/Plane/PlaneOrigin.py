"""PlaneOrigin - Change the origin point of a plane (Grasshopper "Plane Origin")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class PlaneOrigin(Component):
    """Change the origin point of a plane.

    Inputs:
        base: Base plane (Grasshopper Base [item]).
        origin: New origin point of plane (Grasshopper Origin [item]).

    Outputs:
        plane: Plane definition (Grasshopper Plane).

    Notes:
        Grasshopper: Vector > Plane > Plane Origin (Pl Origin).
        pyhopper decisions: none; behaviour matches Grasshopper.
    """

    display_name = "Plane Origin"
    nickname = "Pl Origin"
    gh_guid = "75eec078-a905-47a1-b0d2-0934182b1e3d"

    inputs = [
        InputParam("base", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("origin", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
    ]

    def generate(self, base=AtomicPlane.world_xy(), origin=AtomicPoint.origin()):
        return AtomicPlane(origin=origin, normal=base.normal, x_axis=base.x_axis)
