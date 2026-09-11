"""CullIndex - Remove indexed elements from a list."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class CullIndex(Component):
    """Remove all indexed elements from each list branch.

    ``list`` and ``indices`` are whole-branch (LIST) inputs, ``wrap`` is an
    ITEM input. When ``wrap`` is true, indices wrap into the branch range;
    otherwise out-of-range and negative indices are ignored.
    """

    display_name = "Cull Index"
    nickname = "Cull i"
    gh_guid = "501aecbb-c191-4d13-83d6-7ee32445ac50"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("indices", int, Access.LIST, default=0),
        InputParam("wrap", bool, Access.ITEM, default=False),
    ]
    outputs = [OutputParam("list", access=Access.LIST)]

    def generate(self, list=None, indices=0, wrap=False):
        branch = list if isinstance(list, (tuple, builtins.list)) else [list]
        if not branch:
            return []

        raw_indices = indices if isinstance(indices, builtins.list) else [indices]
        count = len(branch)
        culled = {
            int(index) % count if wrap else int(index)
            for index in raw_indices
            if wrap or 0 <= int(index) < count
        }
        return [item for index, item in enumerate(branch) if index not in culled]
