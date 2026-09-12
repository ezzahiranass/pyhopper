"""OffsetSurfaceLoose - Offset a surface by moving the control points (Grasshopper "Offset Surface Loose")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.SurfaceBuilders import offset_surface_loose
from pyhopper.Core.TypeSystem import SURFACE


class OffsetSurfaceLoose(Component):
    """Offset a surface by moving the control points.

    Inputs:
        surface: Base surface (Grasshopper Surface [item]).
        distance: Offset distance (Grasshopper Distance [item]).
        retrim: Retrim offset (Grasshopper Retrim [item]).

    Outputs:
        surface: Offset result (Grasshopper Surface).

    Notes:
        Grasshopper: Surface > Util > Offset Surface Loose (Offset (L)).
        pyhopper decisions: Grasshopper-verified — every control point moves ``distance`` along the
        unit surface normal at its Greville parameters; ``retrim`` is accepted for parity but pyhopper
        surfaces carry no trims. Grasshopper's defaults (distance 0, retrim on) are kept.
    """

    display_name = "Offset Surface Loose"
    nickname = "Offset (L)"
    gh_guid = "e7e43403-f913-4d83-8aff-5b1c7a7f9fbc"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("distance", float, Access.ITEM, default=0.0),
        InputParam("retrim", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
    ]

    def generate(self, surface=None, distance=0.0, retrim=True):
        return offset_surface_loose(surface, float(distance))
