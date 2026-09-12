"""TransposeSurface - Transpose surface parameterization (swap U and V) (Grasshopper "Transpose Surface")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Nurbs import surface_domain
from pyhopper.Utils.SurfaceBuilders import flip_surface
from pyhopper.Core.TypeSystem import SURFACE


class TransposeSurface(Component):
    """Transpose surface parameterization (swap U and V).

    Inputs:
        surface: Surface to transpose (Grasshopper Surface [item]).

    Outputs:
        surface: Transposed surface (Grasshopper Surface).
        u: {u} domain of transposed surface (Grasshopper U).
        v: {v} domain of transposed surface (Grasshopper V).

    Notes:
        Grasshopper: Surface > Util > Transpose Surface (Transpose).
        pyhopper decisions: none — U and V are swapped (poles transposed, degrees and knots exchanged)
        and the new U and V domains are emitted, like Grasshopper.
    """

    display_name = "Transpose Surface"
    nickname = "Transpose"
    gh_guid = "f0e090d5-7c99-4bce-8830-6a0f1b311e63"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
        OutputParam("u", AtomicInterval),
        OutputParam("v", AtomicInterval),
    ]

    def generate(self, surface=None):
        result = flip_surface(surface)
        (u0, u1), (v0, v1) = surface_domain(result)
        return result, AtomicInterval(u0, u1), AtomicInterval(v0, v1)
