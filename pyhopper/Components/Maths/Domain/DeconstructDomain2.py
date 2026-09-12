"""DeconstructDomain2 - Deconstruct a two-dimensional domain into its component parts (Grasshopper "Deconstruct Domain²")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicInterval2
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DeconstructDomain2(Component):
    """Deconstruct a two-dimensional domain into its component parts.

    Inputs:
        domain: Base domain (Grasshopper Domain [item]).

    Outputs:
        u_component: {u} component of domain (Grasshopper U component).
        v_component: {v} component of domain (Grasshopper V component).

    Notes:
        Grasshopper: Maths > Domain > Deconstruct Domain² (DeDom2).
        pyhopper decisions: none; the U and V intervals are emitted as stored.
    """

    display_name = "Deconstruct Domain²"
    nickname = "DeDom2"
    gh_guid = "f0adfc96-b175-46a6-80c7-2b0ee17395c4"

    inputs = [
        InputParam("domain", AtomicInterval2, Access.ITEM, default=AtomicInterval2()),
    ]
    outputs = [
        OutputParam("u_component", AtomicInterval),
        OutputParam("v_component", AtomicInterval),
    ]

    def generate(self, domain=AtomicInterval2()):
        return domain.u, domain.v
