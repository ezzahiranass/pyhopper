"""RepeatData - Repeat a pattern until it reaches a certain length (Grasshopper "Repeat Data")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class RepeatData(Component):
    """Repeat a pattern until it reaches a certain length.

    Inputs:
        data: Pattern to repeat (Grasshopper Data [list]).
        length: Length of final pattern (Grasshopper Length [item]).

    Outputs:
        data: Repeated data (Grasshopper Data).

    Notes:
        Grasshopper: Sets > Sequence > Repeat Data (Repeat).
        pyhopper decisions: the list repeats (or truncates) to exactly ``length`` items; a negative length
        raises ``ValueError``; an empty list stays empty.
    """

    display_name = "Repeat Data"
    nickname = "Repeat"
    gh_guid = "c40dc145-9e36-4a69-ac1a-6d825c654993"

    inputs = [
        InputParam("data", None, Access.LIST),
        InputParam("length", int, Access.ITEM, default=0),
    ]
    outputs = [
        OutputParam("data", access=Access.LIST),
    ]

    def generate(self, data=None, length=0):
        items = builtins.list(data or [])
        count = int(length)
        if count < 0:
            raise ValueError("Repeat Data length must not be negative")
        if not items:
            return []
        return [items[index % len(items)] for index in range(count)]
