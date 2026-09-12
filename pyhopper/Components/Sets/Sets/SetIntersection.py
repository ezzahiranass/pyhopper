"""SetIntersection - Creates the intersection of two sets (the collection of unique objects present in both sets) (Grasshopper "Set Intersection")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import builtins

from pyhopper.Utils.Items import item_key


class SetIntersection(Component):
    """Creates the intersection of two sets (the collection of unique objects present in both sets).

    Inputs:
        set_a: Data for set Intersection (Grasshopper Set A [list]).
        set_b: Data for set Intersection (Grasshopper Set B [list]).

    Outputs:
        union: The Set Union of all input sets (Grasshopper Union).

    Notes:
        Grasshopper: Sets > Sets > Set Intersection (Intersection).
        pyhopper decisions: the distinct members of B that also occur in A, in B's order
        (Grasshopper-verified: ``[1, 2, 2, 3, 5] ∩ [5, 3, 3, 7]`` is ``[5, 3]``); with one set
        missing the other's distinct members are returned.
    """

    display_name = "Set Intersection"
    nickname = "Intersection"
    gh_guid = "82f19c48-9e73-43a4-ae6c-3a8368099b08"

    inputs = [
        InputParam("set_a", None, Access.LIST, optional=True),
        InputParam("set_b", None, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("union", access=Access.LIST),
    ]

    def generate(self, set_a=None, set_b=None):
        a = builtins.set(item_key(item) for item in (set_a or []))
        b = builtins.set(item_key(item) for item in (set_b or []))
        source = set_b if set_a and set_b else (set_a or set_b or [])
        keep = (a & b) if set_a and set_b else (a | b)
        members, seen = [], builtins.set()
        for item in source:
            key = item_key(item)
            if key in keep and key not in seen:
                seen.add(key)
                members.append(item)
        return members
