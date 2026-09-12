"""CarthesianProduct - Create the Carthesian product for two sets of identical cardinality (Grasshopper "Carthesian Product")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class CarthesianProduct(Component):
    """Create the Carthesian product for two sets of identical cardinality.

    Inputs:
        set_a: First set for carthesian product. (Grasshopper Set A [list]).
        set_b: Second set for carthesian product. (Grasshopper Set B [list]).

    Outputs:
        product: Carthesian product of A and B. (Grasshopper Product).

    Notes:
        Grasshopper: Sets > Sets > Carthesian Product (CProd).
        pyhopper decisions: Grasshopper-verified — despite the name the component pairs the sets up:
        branch ``{path;i}`` holds ``[A[i], B[i]]``; sets of different length raise ``ValueError``
        (Grasshopper reports an error and emits nothing).
    """

    display_name = "Carthesian Product"
    nickname = "CProd"
    gh_guid = "deffaf1e-270a-4c15-a693-9216b68afd4a"

    inputs = [
        InputParam("set_a", None, Access.LIST),
        InputParam("set_b", None, Access.LIST),
    ]
    outputs = [
        OutputParam("product", access=Access.TREE),
    ]

    def generate(self, set_a=None, set_b=None):
        a, b = list(set_a or []), list(set_b or [])
        if len(a) != len(b):
            raise ValueError("CarthesianProduct needs sets of the same length")
        return self.sub_branches([[first, second] for first, second in zip(a, b)])
