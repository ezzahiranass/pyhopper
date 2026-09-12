"""SplitList - Split each list branch at an index."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class SplitList(Component):
    """Split each incoming branch into two lists at an index.

    ``list`` is a whole-branch (LIST) input and ``index`` an ITEM input. The
    split index identifies the first item in ``list_b``. Indices outside the
    branch bounds are clamped to the closest valid split position.
    """

    display_name = "Split List"
    nickname = "Split"
    gh_guid = "9ab93e1a-ebdf-4090-9296-b000cff7b202"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("index", int, Access.ITEM, default=1),
    ]
    outputs = [OutputParam("list_a", access=Access.LIST), OutputParam("list_b", access=Access.LIST)]

    def generate(self, list=None, index=1):
        """Return the portions before and after the split index."""
        branch = list if isinstance(list, (tuple, builtins.list)) else [list]
        split_index = max(0, min(len(branch), int(index)))
        return branch[:split_index], branch[split_index:]
