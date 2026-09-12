"""SetDifference - Create the difference of two sets (the collection of objects present in A but not in B) (Grasshopper "Set Difference")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import builtins

from pyhopper.Utils.Items import item_key


class SetDifference(Component):
    """Create the difference of two sets (the collection of objects present in A but not in B).

    Inputs:
        set_a: Set to subtract from. (Grasshopper Set A [list]).
        set_b: Subtraction set. (Grasshopper Set B [list]).

    Outputs:
        union: The Set Difference of A minus B (Grasshopper Union).

    Notes:
        Grasshopper: Sets > Sets > Set Difference (Difference).
        pyhopper decisions: every item of A whose value is not in B, duplicates in A kept
        (Grasshopper-verified: ``[1, 2, 2, 3, 5] − [5, 3, 7]`` is ``[1, 2, 2]``); membership is by
        type and value, so ``1.0`` and ``"1"`` survive a B containing ``1``.
    """

    display_name = "Set Difference"
    nickname = "Difference"
    gh_guid = "e3b1a10c-4d49-4140-b8e6-0b5732a26c31"

    inputs = [
        InputParam("set_a", None, Access.LIST),
        InputParam("set_b", None, Access.LIST),
    ]
    outputs = [
        OutputParam("union", access=Access.LIST),
    ]

    def generate(self, set_a=None, set_b=None):
        excluded = builtins.set(item_key(item) for item in (set_b or []))
        return [item for item in (set_a or []) if item_key(item) not in excluded]
