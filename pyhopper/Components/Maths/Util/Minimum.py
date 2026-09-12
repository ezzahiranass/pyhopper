"""Minimum - Return the lesser of two items (Grasshopper "Minimum")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Minimum(Component):
    """Return the lesser of two items.

    Inputs:
        a: First item for comparison (Grasshopper A [item]).
        b: Second item for comparison (Grasshopper B [item]).

    Outputs:
        result: The lesser of A and B (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Util > Minimum (Min).
        pyhopper decisions: numeric inputs only (Grasshopper evaluates text as expressions).
    """

    display_name = "Minimum"
    nickname = "Min"
    gh_guid = "57308b30-772d-4919-ac67-e86c18f3a996"

    inputs = [
        InputParam("a", float, Access.ITEM, default=0.0),
        InputParam("b", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, a=0.0, b=0.0):
        return min(float(a), float(b))
