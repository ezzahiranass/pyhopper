"""SplitList - Split each list branch at an index."""

from __future__ import annotations

import builtins
from typing import Any

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _first_int(value: Any, default: int) -> int:
    values = value if isinstance(value, builtins.list) else [value]
    return int(values[0]) if values else default


class SplitList(Component):
    """Split each incoming branch into two lists at an index.

    The split index identifies the first item in ``list_b``. Indices outside
    the branch bounds are clamped to the closest valid split position.
    """

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("index", int, Access.LIST, default=1),
    ]
    outputs = [OutputParam("list_a"), OutputParam("list_b")]

    def generate(self, list=None, index=1):
        """Return the portions before and after the split index."""
        branch = list if isinstance(list, builtins.list) else [list]
        split_index = max(0, min(len(branch), _first_int(index, 1)))
        return branch[:split_index], branch[split_index:]
