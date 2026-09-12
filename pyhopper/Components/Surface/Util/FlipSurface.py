"""FlipSurface - Flip the normals of a surface based on local or remote geometry (Grasshopper "Flip")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicTrimmedSurface
from pyhopper.Utils.SurfaceBuilders import flip_surface, surface_normal_at_centre
from pyhopper.Utils.Vectors import dot
from pyhopper.Core.TypeSystem import SURFACE


class FlipSurface(Component):
    """Flip the normals of a surface based on local or remote geometry.

    Inputs:
        surface: Surface to flip (Grasshopper Surface [item]).
        guide: Optional guide surface to match (Grasshopper Guide [item]).

    Outputs:
        surface: Flipped surface (Grasshopper Surface).
        result: Result: True if surface was flipped (Grasshopper Result).

    Notes:
        Grasshopper: Surface > Util > Flip (Flip).
        pyhopper decisions: flipping swaps the U and V directions of the pole grid, which reverses the
        normal (Grasshopper only toggles an orientation flag on the face); with a guide the surface is
        flipped only when the two normals at the domain centres oppose each other; ``result`` says
        whether it was flipped.
    """

    display_name = "Flip"
    nickname = "Flip"
    gh_guid = "c3d1f2b8-8596-4e8d-8861-c28ba8ffb4f4"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("guide", SURFACE, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
        OutputParam("result", bool),
    ]

    def generate(self, surface=None, guide=None):
        base = surface.surface if isinstance(surface, AtomicTrimmedSurface) else surface
        if guide is not None:
            other = guide.surface if isinstance(guide, AtomicTrimmedSurface) else guide
            if dot(surface_normal_at_centre(base), surface_normal_at_centre(other)) >= 0.0:
                return base, False
        return flip_surface(base), True
