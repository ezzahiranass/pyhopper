"""DeconstructDomain2Num - Deconstruct a two-dimensional domain into four numbers (Grasshopper "Deconstruct Domain²")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval2
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DeconstructDomain2Num(Component):
    """Deconstruct a two-dimensional domain into four numbers.

    Inputs:
        domain: Base domain (Grasshopper Domain [item]).

    Outputs:
        u_min: Lower limit of domain in {u} direction (Grasshopper U min).
        u_max: Upper limit of domain in {u} direction (Grasshopper U max).
        v_min: Lower limit of domain in {v} direction (Grasshopper V min).
        v_max: Upper limit of domain in {v} direction (Grasshopper V max).

    Notes:
        Grasshopper: Maths > Domain > Deconstruct Domain² (DeDom2Num).
        pyhopper decisions: none; the four bounds are emitted as stored (reversed domains keep their order).
    """

    display_name = "Deconstruct Domain²"
    nickname = "DeDom2Num"
    gh_guid = "47c30f9d-b685-4d4d-9b20-5b60e48d5af8"

    inputs = [
        InputParam("domain", AtomicInterval2, Access.ITEM, default=AtomicInterval2()),
    ]
    outputs = [
        OutputParam("u_min", float),
        OutputParam("u_max", float),
        OutputParam("v_min", float),
        OutputParam("v_max", float),
    ]

    def generate(self, domain=AtomicInterval2()):
        return float(domain.u.start), float(domain.u.end), float(domain.v.start), float(domain.v.end)
