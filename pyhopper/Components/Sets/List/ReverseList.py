"""ReverseList - Reverse the item order of each list branch."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ReverseList(Component):
    """Reverse every incoming branch while preserving its DataTree path."""

    inputs = [InputParam("list", None, Access.LIST)]
    outputs = [OutputParam("list", access=Access.LIST)]

    def generate(self, list=None):
        """Return the incoming branch in reverse order."""
        branch = list if isinstance(list, builtins.list) else [list]
        return branch[::-1]
