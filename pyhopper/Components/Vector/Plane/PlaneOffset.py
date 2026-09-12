"""PlaneOffset - Offset a plane (Grasshopper "Plane Offset")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Vectors import translate


class PlaneOffset(Component):
    """Offset a plane.

    Inputs:
        base_plane: Base plane for offset (Grasshopper Base Plane [item]).
        offset: Offset distance (along base plane z-axis (Grasshopper Offset [item]).

    Outputs:
        plane: Offset plane (Grasshopper Plane).

    Notes:
        Grasshopper: Vector > Plane > Plane Offset (Pl Offset).
        pyhopper decisions: none; the origin moves ``offset`` along the normal (default 1), as in Grasshopper.
    """

    display_name = "Plane Offset"
    nickname = "Pl Offset"
    gh_guid = "3a0c7bda-3d22-4588-8bab-03f57a52a6ea"

    inputs = [
        InputParam("base_plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("offset", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
    ]

    def generate(self, base_plane=AtomicPlane.world_xy(), offset=1.0):
        return AtomicPlane(translate(base_plane.origin, base_plane.normal, float(offset)), base_plane.normal, base_plane.x_axis)
