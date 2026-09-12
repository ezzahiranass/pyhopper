"""Dimensions - Get the approximate dimensions of a surface (Grasshopper "Dimensions")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicTrimmedSurface
from pyhopper.Utils.SurfaceBuilders import surface_dimensions
from pyhopper.Core.TypeSystem import SURFACE


def _untrimmed(surface):
    return surface.surface if isinstance(surface, AtomicTrimmedSurface) else surface


class Dimensions(Component):
    """Get the approximate dimensions of a surface.

    Inputs:
        surface: Surface to measure (Grasshopper Surface [item]).

    Outputs:
        u_dimension: Approximate dimension in U direction (Grasshopper U dimension).
        v_dimension: Approximate dimension in V direction (Grasshopper V dimension).

    Notes:
        Grasshopper: Surface > Analysis > Dimensions (Dim).
        pyhopper decisions: the longest control-polygon length in each direction — what Grasshopper reports as the
        approximate size (exact for planar surfaces).
    """

    display_name = "Dimensions"
    nickname = "Dim"
    gh_guid = "f241e42e-8983-4ed3-b869-621c07630b00"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
    ]
    outputs = [
        OutputParam("u_dimension", float),
        OutputParam("v_dimension", float),
    ]

    def generate(self, surface=None):
        return surface_dimensions(_untrimmed(surface))
