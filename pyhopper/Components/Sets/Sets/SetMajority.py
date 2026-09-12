"""SetMajority - Determine majority member presence amongst three sets (Grasshopper "Set Majority")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Items import item_key


class SetMajority(Component):
    """Determine majority member presence amongst three sets.

    Inputs:
        set_a: First set. (Grasshopper Set A [list]).
        set_b: Second set. (Grasshopper Set B [list]).
        set_c: Third set. (Grasshopper Set C [list]).

    Outputs:
        result: Set containing all unique elements in that occur in at least two of the input sets. (Grasshopper Result).

    Notes:
        Grasshopper: Sets > Sets > Set Majority (Majority).
        pyhopper decisions: Grasshopper-verified — the distinct items present in at least two sets,
        ordered as A∩B, then the new members of B∩C, then those of A∩C; membership is by type and
        value.
    """

    display_name = "Set Majority"
    nickname = "Majority"
    gh_guid = "d4136a7b-7422-4660-9404-640474bd2725"

    inputs = [
        InputParam("set_a", None, Access.LIST),
        InputParam("set_b", None, Access.LIST),
        InputParam("set_c", None, Access.LIST),
    ]
    outputs = [
        OutputParam("result", access=Access.LIST),
    ]

    def generate(self, set_a=None, set_b=None, set_c=None):
        a, b, c = list(set_a or []), list(set_b or []), list(set_c or [])
        keys = [{item_key(item) for item in members} for members in (a, b, c)]
        result, seen = [], builtins.set()
        for members, other in ((a, keys[1]), (b, keys[2]), (a, keys[2])):
            for item in members:
                key = item_key(item)
                if key in other and key not in seen:
                    seen.add(key)
                    result.append(item)
        return result
