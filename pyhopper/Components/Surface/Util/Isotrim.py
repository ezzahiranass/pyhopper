"""Isotrim - Extract an isoparametric subset of a surface (Grasshopper "Isotrim")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval2
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.NurbsEditing import sub_surface
from pyhopper.Core.TypeSystem import SURFACE


class Isotrim(Component):
    """Extract an isoparametric subset of a surface.

    Inputs:
        surface: Base surface (Grasshopper Surface [item]).
        domain: Domain of subset (Grasshopper Domain [item]).

    Outputs:
        surface: Subset of base surface (Grasshopper Surface).

    Notes:
        Grasshopper: Surface > Util > Isotrim (SubSrf).
        pyhopper decisions: Grasshopper-verified — the sub-surface over the domain (each interval
        sorted and clipped to the surface) by knot insertion, keeping the parameterisation. Grasshopper
        has no default domain; pyhopper's [0, 1]² is the whole of a unit-domain surface.
    """

    display_name = "Isotrim"
    nickname = "SubSrf"
    gh_guid = "6a9ccaab-1b03-484e-bbda-be9c81584a66"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("domain", AtomicInterval2, Access.ITEM, default=AtomicInterval2()),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
    ]

    def generate(self, surface=None, domain=AtomicInterval2()):
        return sub_surface(surface, (float(domain.u.start), float(domain.u.end)), (float(domain.v.start), float(domain.v.end)))
