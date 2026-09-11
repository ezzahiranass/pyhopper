"""PlaneSurface - Create a plane surface (Grasshopper "Plane Surface")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.SurfaceBuilders import plane_surface
from pyhopper.Core.TypeSystem import SURFACE


class PlaneSurface(Component):
    """Create a plane surface.

    Inputs:
        plane: Surface base plane (Grasshopper Plane [item]).
        x_size: Dimensions in X direction (Grasshopper X Size [item]).
        y_size: Dimensions in Y direction (Grasshopper Y Size [item]).

    Outputs:
        surface: Resulting plane surface (Grasshopper Plane).

    Notes:
        Grasshopper: Surface > Primitive > Plane Surface (PlaneSrf).
        pyhopper decisions: a degree-1 surface whose knot domains are the size domains, like Grasshopper; Grasshopper
        defaults ``x_size = y_size = [-10, 10]``; empty domains raise ``ValueError``.
    """

    display_name = "Plane Surface"
    nickname = "PlaneSrf"
    gh_guid = "439a55a5-2f9e-4f66-9de2-32f24fec2ef5"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("x_size", AtomicInterval, Access.ITEM, default=AtomicInterval(-10.0, 10.0)),
        InputParam("y_size", AtomicInterval, Access.ITEM, default=AtomicInterval(-10.0, 10.0)),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), x_size=AtomicInterval(-10.0, 10.0), y_size=AtomicInterval(-10.0, 10.0)):
        return plane_surface(plane, x_size, y_size)
