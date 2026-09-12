"""Untrim - Remove all trim curves from a surface (Grasshopper "Untrim")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicTrimmedSurface
from pyhopper.Core.TypeSystem import SURFACE


class Untrim(Component):
    """Remove all trim curves from a surface.

    Inputs:
        surface: Base surface (Grasshopper Surface [item]).

    Outputs:
        surface: Untrimmed surface (Grasshopper Surface).

    Notes:
        Grasshopper: Surface > Util > Untrim (Untrim).
        pyhopper decisions: none; a trimmed surface returns its underlying surface, an untrimmed one passes through.
    """

    display_name = "Untrim"
    nickname = "Untrim"
    gh_guid = "fa92858a-a180-4545-ad4d-0dc644b3a2a8"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
    ]

    def generate(self, surface=None):
        return surface.surface if isinstance(surface, AtomicTrimmedSurface) else surface
