"""ConstructDomain2 - Create a two-dimensional domain from two simple domains (Grasshopper "Construct Domain²")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicInterval2
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ConstructDomain2(Component):
    """Create a two-dimensional domain from two simple domains.

    Inputs:
        domain_u: Domain in {u} direction (Grasshopper Domain U [item]).
        domain_v: Domain in {v} direction (Grasshopper Domain V [item]).

    Outputs:
        domain: Two dimensional numeric domain of {u} and {v} (Grasshopper 2D Domain).

    Notes:
        Grasshopper: Maths > Domain > Construct Domain² (Dom²).
        pyhopper decisions: none; the two intervals are kept as given (reversed domains stay reversed).
    """

    display_name = "Construct Domain²"
    nickname = "Dom²"
    gh_guid = "8555a743-36c1-42b8-abcc-06d9cb94519f"

    inputs = [
        InputParam("domain_u", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
        InputParam("domain_v", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
    ]
    outputs = [
        OutputParam("domain", AtomicInterval2),
    ]

    def generate(self, domain_u=AtomicInterval(0.0, 1.0), domain_v=AtomicInterval(0.0, 1.0)):
        return AtomicInterval2(domain_u, domain_v)
