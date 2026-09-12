"""OffsetSurface - Offset a surface by a fixed amount (Grasshopper "Offset Surface")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Differential import offset_surface
from pyhopper.Core.TypeSystem import SURFACE


class OffsetSurface(Component):
    """Offset a surface by a fixed amount.

    Inputs:
        surface: Base surface (Grasshopper Surface [item]).
        distance: Offset distance (Grasshopper Distance [item]).
        retrim: Retrim offset (Grasshopper Retrim [item]).

    Outputs:
        surface: Offset result (Grasshopper Surface).

    Notes:
        Grasshopper: Surface > Util > Offset Surface (Offset).
        pyhopper decisions: planar surfaces translate exactly along their normal (as Grasshopper
        does); curved surfaces are approximated by interpolating a dense grid of offset points, where
        Rhino refits with its own tolerance-driven algorithm — only the structure is comparable.
        ``retrim`` is accepted for parity (pyhopper surfaces carry no trims); Grasshopper's defaults
        (distance 0, retrim on) are kept.
    """

    display_name = "Offset Surface"
    nickname = "Offset"
    gh_guid = "b25c5762-f90e-4839-9fc5-74b74ab42b1e"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("distance", float, Access.ITEM, default=0.0),
        InputParam("retrim", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
    ]

    def generate(self, surface=None, distance=0.0, retrim=True):
        return offset_surface(surface, float(distance))
