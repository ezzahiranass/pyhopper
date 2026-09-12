"""DeleteConsecutive - Delete consecutive similar members in a set (Grasshopper "Delete Consecutive")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import builtins

from pyhopper.Utils.Items import item_key


class DeleteConsecutive(Component):
    """Delete consecutive similar members in a set.

    Inputs:
        set: Set to operate on. (Grasshopper Set [list]).
        wrap: If true, the last and first member are considered to be adjacent. (Grasshopper Wrap [item]).

    Outputs:
        set: Set with consecutive identical members removed. (Grasshopper Set).
        count: Number of members removed. (Grasshopper Count).

    Notes:
        Grasshopper: Sets > Sets > Delete Consecutive (DCon).
        pyhopper decisions: consecutive equal items collapse to one (equality by type and value);
        with ``wrap`` the run at the end also merges into the run at the start; ``count`` is the
        number of items removed. Grasshopper-verified.
    """

    display_name = "Delete Consecutive"
    nickname = "DCon"
    gh_guid = "190d042c-2270-4bc1-81c0-4f90c170c9c9"

    inputs = [
        InputParam("set", None, Access.LIST),
        InputParam("wrap", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("set", access=Access.LIST),
        OutputParam("count", int),
    ]

    def generate(self, set=None, wrap=False):
        items = builtins.list(set or [])
        kept = []
        for item in items:
            if not kept or item_key(kept[-1]) != item_key(item):
                kept.append(item)
        if wrap and len(kept) > 1 and item_key(kept[-1]) == item_key(kept[0]):
            kept.pop()
        return kept, len(items) - len(kept)
