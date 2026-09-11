"""ShiftList - Offset items within each list branch."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ShiftList(Component):
    """Shift each incoming branch by an integer offset.

    ``list`` is a whole-branch (LIST) input; ``shift`` and ``wrap`` are ITEM
    inputs, so several shift values in one branch produce one shifted list per
    value in sub-branches. Positive offsets begin the result later in the
    branch. With ``wrap`` enabled, shifted-out items cycle to the opposite end.
    """

    display_name = "Shift List"
    nickname = "Shift"
    gh_guid = "4fdfe351-6c07-47ce-9fb9-be027fb62186"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("shift", int, Access.ITEM, default=1),
        InputParam("wrap", bool, Access.ITEM, default=True),
    ]
    outputs = [OutputParam("list", access=Access.LIST)]

    def generate(self, list=None, shift=1, wrap=True):
        """Return the shifted incoming branch."""
        branch = list if isinstance(list, (tuple, builtins.list)) else [list]
        if not branch:
            return []

        offset = int(shift)
        if wrap:
            offset %= len(branch)
            return branch[offset:] + branch[:offset]

        if offset >= len(branch) or offset <= -len(branch):
            return []
        if offset > 0:
            return branch[offset:]
        if offset < 0:
            return branch[:offset]
        return branch
