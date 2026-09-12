"""ReverseSurface - Reverse directions of surface parameterization (U, V, and W) (Grasshopper "Reverse Surface")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.SurfaceBuilders import reverse_surface
from pyhopper.Core.TypeSystem import SURFACE


class ReverseSurface(Component):
    """Reverse directions of surface parameterization (U, V, and W).

    Inputs:
        surface: Surface to reverse (Grasshopper Surface [item]).
        u: Reverse the {u} direction of the surface parameterization. (Grasshopper U [item]).
        v: Reverse the {v} direction of the surface parameterization. (Grasshopper V [item]).
        w: Reverse the {w} direction (also known as the normal) of the surface parameterization. (Grasshopper W [item]).

    Outputs:
        surface: Reversed surface (Grasshopper Surface).

    Notes:
        Grasshopper: Surface > Util > Reverse Surface (Reverse Srf).
        pyhopper decisions: Grasshopper-verified — reversing U or V flips the poles along that axis
        and turns the knot domain ``[a, b]`` into ``[-b, -a]`` like Rhino; ``w`` (the normal flip) has
        no effect on the surface data, in Grasshopper or here.
    """

    display_name = "Reverse Surface"
    nickname = "Reverse Srf"
    gh_guid = "847cf05e-e195-4bc7-b472-e05459b9792b"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("u", bool, Access.ITEM, default=False),
        InputParam("v", bool, Access.ITEM, default=False),
        InputParam("w", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
    ]

    def generate(self, surface=None, u=False, v=False, w=False):
        return reverse_surface(surface, bool(u), bool(v))
