"""Dispatch - Dispatch the items in a list into two target lists (Grasshopper "Dispatch")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._lists import cycle


class Dispatch(Component):
    """Dispatch the items in a list into two target lists.

    Inputs:
        list: List to filter (Grasshopper List [list]).
        dispatch_pattern: Dispatch pattern (Grasshopper Dispatch pattern [list]).

    Outputs:
        list_a: Dispatch target for True values (Grasshopper List A).
        list_b: Dispatch target for False values (Grasshopper List B).

    Notes:
        Grasshopper: Sets > List > Dispatch (Dispatch).
        pyhopper decisions: the pattern repeats along the list (Grasshopper default ``True, False``); an
        empty pattern dispatches nothing, like Grasshopper.
    """

    display_name = "Dispatch"
    nickname = "Dispatch"
    gh_guid = "d8332545-21b2-4716-96e3-8559a9876e17"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("dispatch_pattern", bool, Access.LIST, default=[True, False]),
    ]
    outputs = [
        OutputParam("list_a", access=Access.LIST),
        OutputParam("list_b", access=Access.LIST),
    ]

    def generate(self, list=None, dispatch_pattern=(True, False)):
        items = builtins.list(list or [])
        flags = cycle(builtins.list(dispatch_pattern or []), len(items))
        list_a = [item for item, flag in zip(items, flags) if flag]
        list_b = [item for item, flag in zip(items, flags) if not flag]
        return list_a, list_b
