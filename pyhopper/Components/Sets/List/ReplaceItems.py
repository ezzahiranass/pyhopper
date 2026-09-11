"""ReplaceItems - Replace certain items in a list (Grasshopper "Replace Items")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._lists import resolve_index


class ReplaceItems(Component):
    """Replace certain items in a list.

    Inputs:
        list: List to modify (Grasshopper List [list]).
        item: Items to replace with. If no items are supplied, nulls will be inserted. (Grasshopper Item [list]).
        indices: Replacement index for each item (Grasshopper Indices [list]).
        wrap: If true, indices will be wrapped (Grasshopper Wrap [item]).

    Outputs:
        list: List with replaced values (Grasshopper List).

    Notes:
        Grasshopper: Sets > List > Replace Items (Replace).
        pyhopper decisions: items repeat over the indices; an index outside the list raises ``IndexError``
        unless ``wrap`` is set (Grasshopper reports an error and emits nothing); without
        indices or items the list passes through unchanged.
    """

    display_name = "Replace Items"
    nickname = "Replace"
    gh_guid = "7a218bfb-b93d-4c1f-83d3-5a0b909dd60b"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("item", None, Access.LIST, optional=True),
        InputParam("indices", int, Access.LIST, optional=True),
        InputParam("wrap", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("list", access=Access.LIST),
    ]

    def generate(self, list=None, item=None, indices=None, wrap=False):
        result = builtins.list(list or [])
        values = builtins.list(item or [])
        positions = [int(index) for index in (indices or [])]
        if not values or not positions:
            return result
        for order, position in enumerate(positions):
            result[resolve_index(position, len(result), wrap, "Replace Items")] = values[order % len(values)]
        return result
