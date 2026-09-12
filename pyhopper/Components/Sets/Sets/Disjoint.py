"""Disjoint - Test whether two sets are disjoint (Grasshopper "Disjoint")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Items import item_key


class Disjoint(Component):
    """Test whether two sets are disjoint.

    Inputs:
        set_a: First set. (Grasshopper Set A [list]).
        set_b: Second set. (Grasshopper Set B [list]).

    Outputs:
        result: True if none of the items in A occur in B. (Grasshopper Result).

    Notes:
        Grasshopper: Sets > Sets > Disjoint (Disjoint).
        pyhopper decisions: true when no item of A occurs in B (an empty set is disjoint from
        anything); membership is by type and value like Grasshopper.
    """

    display_name = "Disjoint"
    nickname = "Disjoint"
    gh_guid = "81800098-1060-4e2b-80d4-17f835cc825f"

    inputs = [
        InputParam("set_a", None, Access.LIST),
        InputParam("set_b", None, Access.LIST),
    ]
    outputs = [
        OutputParam("result", bool),
    ]

    def generate(self, set_a=None, set_b=None):
        keys_b = {item_key(item) for item in (set_b or [])}
        return not any(item_key(item) in keys_b for item in (set_a or []))
