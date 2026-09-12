"""SetUnion - Creates the union of two sets (the collection of unique objects present in either set) (Grasshopper "Set Union")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Items import item_key


class SetUnion(Component):
    """Creates the union of two sets (the collection of unique objects present in either set).

    Inputs:
        set_a: Data for set Union. (Grasshopper Set A [list]).
        set_b: Data for set Union. (Grasshopper Set B [list]).

    Outputs:
        union: The Set Union of A and B. (Grasshopper Union).

    Notes:
        Grasshopper: Sets > Sets > Set Union (SUnion).
        pyhopper decisions: distinct members of A then the new members of B, first-appearance
        order; membership is by type and value (``1`` and ``1.0`` differ) like Grasshopper.
    """

    display_name = "Set Union"
    nickname = "SUnion"
    gh_guid = "8eed5d78-7810-4ba1-968e-8a1f1db98e39"

    inputs = [
        InputParam("set_a", None, Access.LIST, optional=True),
        InputParam("set_b", None, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("union", access=Access.LIST),
    ]

    def generate(self, set_a=None, set_b=None):
        members, seen = [], set()
        for item in [*(set_a or []), *(set_b or [])]:
            key = item_key(item)
            if key not in seen:
                seen.add(key)
                members.append(item)
        return members
