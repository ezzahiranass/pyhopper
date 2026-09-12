"""SubSet - Test two sets for inclusion (Grasshopper "SubSet")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Items import item_key


class SubSet(Component):
    """Test two sets for inclusion.

    Inputs:
        set_a: Super set. (Grasshopper Set A [list]).
        set_b: Sub set. (Grasshopper Set B [list]).

    Outputs:
        result: True if all items in B are present in A. (Grasshopper Result).

    Notes:
        Grasshopper: Sets > Sets > SubSet (SubSet).
        pyhopper decisions: Grasshopper-verified — true when every item of B occurs in A (B is a
        subset of A; equal sets qualify, an empty B always does); membership is by type and value.
    """

    display_name = "SubSet"
    nickname = "SubSet"
    gh_guid = "4cfc0bb0-0745-4772-a520-39f9bf3d99bc"

    inputs = [
        InputParam("set_a", None, Access.LIST),
        InputParam("set_b", None, Access.LIST),
    ]
    outputs = [
        OutputParam("result", bool),
    ]

    def generate(self, set_a=None, set_b=None):
        keys_a = {item_key(item) for item in (set_a or [])}
        return all(item_key(item) in keys_a for item in (set_b or []))
