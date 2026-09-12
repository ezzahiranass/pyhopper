"""SymmetricDifference - Create the symmetric difference of two sets (the collection of objects present in A or B but not both) (Grasshopper "Set Difference (S)")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Items import item_key


class SymmetricDifference(Component):
    """Create the symmetric difference of two sets (the collection of objects present in A or B but not both).

    Inputs:
        set_a: First set for symmetric difference. (Grasshopper Set A [list]).
        set_b: Second set for symmetric difference. (Grasshopper Set B [list]).

    Outputs:
        symmetric_difference: The symmetric difference between A and B. (Grasshopper ExDifference).

    Notes:
        Grasshopper: Sets > Sets > Set Difference (S) (ExDiff).
        pyhopper decisions: Grasshopper-verified — the items of A that do not occur in B (duplicates
        kept, in order) followed by the items of B that do not occur in A; membership is by type and
        value (``1`` and ``1.0`` differ).
    """

    display_name = "Set Difference (S)"
    nickname = "ExDiff"
    gh_guid = "d2461702-3164-4894-8c10-ed1fc4b52965"

    inputs = [
        InputParam("set_a", None, Access.LIST),
        InputParam("set_b", None, Access.LIST),
    ]
    outputs = [
        OutputParam("symmetric_difference", access=Access.LIST),
    ]

    def generate(self, set_a=None, set_b=None):
        a, b = list(set_a or []), list(set_b or [])
        keys_a, keys_b = {item_key(item) for item in a}, {item_key(item) for item in b}
        return [item for item in a if item_key(item) not in keys_b] + [item for item in b if item_key(item) not in keys_a]
