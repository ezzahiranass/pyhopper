"""DuplicateData - Duplicate data a predefined number of times (Grasshopper "Duplicate Data")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DuplicateData(Component):
    """Duplicate data a predefined number of times.

    Inputs:
        data: Data to duplicate (Grasshopper Data [list]).
        number: Number of duplicates (Grasshopper Number [item]).
        order: Retain list order (Grasshopper Order [item]).

    Outputs:
        data: Duplicated data (Grasshopper Data).

    Notes:
        Grasshopper: Sets > Sequence > Duplicate Data (Dup).
        pyhopper decisions: ``order = True`` repeats the whole list (``a b a b``), ``False`` repeats each item
        in place (``a a b b``); Grasshopper defaults ``number = 2``, ``order = True``;
        a negative number raises ``ValueError``.
    """

    display_name = "Duplicate Data"
    nickname = "Dup"
    gh_guid = "dd8134c0-109b-4012-92be-51d843edfff7"

    inputs = [
        InputParam("data", None, Access.LIST),
        InputParam("number", int, Access.ITEM, default=2),
        InputParam("order", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("data", access=Access.LIST),
    ]

    def generate(self, data=None, number=2, order=True):
        items = builtins.list(data or [])
        copies = int(number)
        if copies < 0:
            raise ValueError("Duplicate Data number must not be negative")
        if order:
            return items * copies
        return [item for item in items for _ in range(copies)]
