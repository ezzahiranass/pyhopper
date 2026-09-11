"""SiftPattern - Sift elements in a list using a repeating index pattern (Grasshopper "Sift Pattern")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._lists import cycle


class SiftPattern(Component):
    """Sift elements in a list using a repeating index pattern.

    Inputs:
        list: List to sift (Grasshopper List [list]).
        sift_pattern: Sifting pattern (Grasshopper Sift Pattern [list]).

    Outputs:
        output_0: Output for sift index 0 (Grasshopper Output 0).
        output_1: Output for sift index 1 (Grasshopper Output 1).

    Notes:
        Grasshopper: Sets > List > Sift Pattern (Sift).
        pyhopper decisions: outputs keep the list's index alignment with ``None`` where an item went to
        the other output (Grasshopper nulls); Grasshopper default pattern ``0, 0, 1, 1``;
        pattern values other than 0 and 1 raise ``ValueError`` because pyhopper exposes
        two outputs (Grasshopper discards those items with a warning).
    """

    display_name = "Sift Pattern"
    nickname = "Sift"
    gh_guid = "3249222f-f536-467a-89f4-f0353fba455a"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("sift_pattern", int, Access.LIST, default=[0, 0, 1, 1]),
    ]
    outputs = [
        OutputParam("output_0", access=Access.LIST),
        OutputParam("output_1", access=Access.LIST),
    ]

    def generate(self, list=None, sift_pattern=(0, 0, 1, 1)):
        items = builtins.list(list or [])
        sequence = [int(index) for index in (sift_pattern or [])]
        if items and not sequence:
            raise ValueError("Sift Pattern needs at least one pattern value")
        targets = cycle(sequence, len(items))
        output_0 = []
        output_1 = []
        for item, target in zip(items, targets):
            if target == 0:
                output_0.append(item)
                output_1.append(None)
            elif target == 1:
                output_0.append(None)
                output_1.append(item)
            else:
                raise ValueError(f"Sift Pattern index {target} needs an output that pyhopper does not expose (0 or 1)")
        return output_0, output_1
