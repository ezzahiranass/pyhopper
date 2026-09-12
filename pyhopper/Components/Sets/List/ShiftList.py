"""ShiftList - Offset items within each list branch."""

from __future__ import annotations

import builtins
from typing import Any

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _first(value: Any, default: Any) -> Any:
    values = value if isinstance(value, builtins.list) else [value]
    return values[0] if values else default


class ShiftList(Component):
    """Shift each incoming branch by an integer offset.

    Positive offsets begin the result later in the branch. With ``wrap``
    enabled, shifted-out items cycle to the opposite end.
    """

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("shift", int, Access.LIST, default=1),
        InputParam("wrap", bool, Access.LIST, default=True),
    ]
    outputs = [OutputParam("list")]

    def generate(self, list=None, shift=1, wrap=True):
        """Return the shifted incoming branch."""
        branch = list if isinstance(list, builtins.list) else [list]
        if not branch:
            return []

        offset = int(_first(shift, 1))
        if bool(_first(wrap, True)):
            offset %= len(branch)
            return branch[offset:] + branch[:offset]

        if offset >= len(branch) or offset <= -len(branch):
            return []
        if offset > 0:
            return branch[offset:]
        if offset < 0:
            return branch[:offset]
        return branch
