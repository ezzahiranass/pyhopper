"""ListItem - Select one item from a list branch by index."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ListItem(Component):
    """Select an item from each input branch by index.

    ``list`` is read as a whole branch (LIST access) while ``index`` and
    ``wrap`` are ITEM inputs, so several indices in one branch yield several
    items in the same output branch. ``wrap`` cycles out-of-range indices
    around the branch length; without it an out-of-range index yields nothing.
    """

    display_name = "List Item"
    nickname = "Item"
    gh_guid = "59daf374-bc21-4a5e-8282-5504fb7ae9ae"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("index", int, Access.ITEM, default=0),
        InputParam("wrap", bool, Access.ITEM, default=False),
    ]
    outputs = [OutputParam("item")]

    def generate(self, list=None, index=0, wrap=False):
        """Return the item at ``index`` from the incoming branch."""
        branch = list if isinstance(list, (tuple, builtins.list)) else [list]
        count = len(branch)
        if count == 0:
            return Component.NO_OUTPUT

        resolved_index = int(index) % count if wrap else int(index)
        if 0 <= resolved_index < count:
            return branch[resolved_index]
        return Component.NO_OUTPUT
