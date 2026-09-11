"""InsertItems - Insert a collection of items into a list (Grasshopper "Insert Items")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._lists import pad_to


class InsertItems(Component):
    """Insert a collection of items into a list.

    Inputs:
        list: List to modify (Grasshopper List [list]).
        item: Items to insert. If no items are supplied, nulls will be inserted. (Grasshopper Item [list]).
        indices: Insertion index for each item (Grasshopper Indices [list]).
        wrap: If true, indices will be wrapped (Grasshopper Wrap [item]).

    Outputs:
        list: List with inserted values (Grasshopper List).

    Notes:
        Grasshopper: Sets > List > Insert Items (Ins).
        pyhopper decisions: indices address positions in the result and are processed from the highest
        down, items repeat over the indices (``None`` is inserted when no items are given),
        positions past the end are padded with ``None`` (Grasshopper nulls) and ``wrap`` takes an
        index modulo ``len + 1``; Grasshopper default ``wrap = True``.
    """

    display_name = "Insert Items"
    nickname = "Ins"
    gh_guid = "e2039b07-d3f3-40f8-af88-d74fed238727"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("item", None, Access.LIST, optional=True),
        InputParam("indices", int, Access.LIST),
        InputParam("wrap", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("list", access=Access.LIST),
    ]

    def generate(self, list=None, item=None, indices=None, wrap=True):
        result = builtins.list(list or [])
        values = builtins.list(item) if item else [None]  # Grasshopper inserts nulls when no items are supplied
        positions = [int(index) for index in (indices or [])]
        if not positions:
            return result
        slots = len(result) + 1
        pairs = []
        for order, position in enumerate(positions):
            if wrap:
                position %= slots
            elif position < 0:
                raise IndexError(f"Insert Items index {position} is negative; enable wrap to count from the end")
            pairs.append((position, values[order % len(values)]))
        pairs.sort(key=lambda pair: pair[0])
        for position, value in reversed(pairs):
            pad_to(result, position)
            result.insert(position, value)
        return result
