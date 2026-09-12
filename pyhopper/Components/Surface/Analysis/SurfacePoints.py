"""SurfacePoints - Get the control-points of a Nurbs Surface (Grasshopper "Surface Points")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicTrimmedSurface
from pyhopper.Utils.SurfaceBuilders import surface_control_points
from pyhopper.Core.TypeSystem import SURFACE


class SurfacePoints(Component):
    """Get the control-points of a Nurbs Surface.

    Inputs:
        surface: Surface for control-point extraction (Grasshopper Surface [item]).

    Outputs:
        points: Control point locations (Grasshopper Points).
        weights: Control point weights (Grasshopper Weights).
        greville: Greville uv points (Grasshopper Greville).
        u_count: Number of points along U direction (Grasshopper U Count).
        v_count: Number of points along V direction (Grasshopper V Count).

    Notes:
        Grasshopper: Surface > Analysis > Surface Points (SrfPt).
        pyhopper decisions: points, weights and Greville (u, v, 0) parameter points in Grasshopper's order (u outer,
        v inner); trimmed surfaces report their underlying surface.
    """

    display_name = "Surface Points"
    nickname = "SrfPt"
    gh_guid = "15128198-399d-4d6c-9586-1f65db3ce7bf"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("weights", float, access=Access.LIST),
        OutputParam("greville", AtomicPoint, access=Access.LIST),
        OutputParam("u_count", int),
        OutputParam("v_count", int),
    ]

    def generate(self, surface=None):
        return surface_control_points(surface.surface if isinstance(surface, AtomicTrimmedSurface) else surface)
