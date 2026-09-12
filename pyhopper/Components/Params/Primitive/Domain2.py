"""Domain2 - Contains a collection of two-dimensional domains (Grasshopper "Domain²")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval2
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Domain2(Component):
    """Contains a collection of two-dimensional domains.

    Inputs:
        domain: Two-dimensional domains to contain (Grasshopper Domain²).

    Outputs:
        domain: The same domains (Grasshopper Domain²).

    Notes:
        Grasshopper: Params > Primitive > Domain² (Domain²).
        pyhopper decisions: a container like ``Domain``; two-dimensional domains are ``AtomicInterval2``
        atoms (a U and a V interval), the K6 unlock of the component roadmap.
    """

    display_name = "Domain²"
    nickname = "Domain²"
    gh_guid = "90744326-eb53-4a0e-b7ef-4b45f5473d6e"

    inputs = [InputParam("domain", AtomicInterval2, Access.ITEM)]
    outputs = [OutputParam("domain", AtomicInterval2)]

    def generate(self, domain=None):
        return domain
