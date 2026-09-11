"""CullPattern - Cull (remove) elements in a list using a repeating bit mask (Grasshopper "Cull Pattern")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._lists import cycle


class CullPattern(Component):
    """Cull (remove) elements in a list using a repeating bit mask.

    Inputs:
        list: List to cull (Grasshopper List [list]).
        cull_pattern: Culling pattern (Grasshopper Cull Pattern [list]).

    Outputs:
        list: Culled list (Grasshopper List).

    Notes:
        Grasshopper: Sets > Sequence > Cull Pattern (Cull).
        pyhopper decisions: the pattern repeats along the list and ``True`` keeps an item (Grasshopper default
        ``False, False, True, True``); an empty pattern culls everything, like Grasshopper.
    """

    display_name = "Cull Pattern"
    nickname = "Cull"
    gh_guid = "008e9a6f-478a-4813-8c8a-546273bc3a6b"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("cull_pattern", bool, Access.LIST, default=[False, False, True, True]),
    ]
    outputs = [
        OutputParam("list", access=Access.LIST),
    ]

    def generate(self, list=None, cull_pattern=(False, False, True, True)):
        items = builtins.list(list or [])
        flags = cycle(builtins.list(cull_pattern or []), len(items))
        return [item for item, flag in zip(items, flags) if flag]
