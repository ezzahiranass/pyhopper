"""GateMajority - Calculates the majority vote among three booleans (Grasshopper "Gate Majority")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class GateMajority(Component):
    """Calculates the majority vote among three booleans.

    Inputs:
        a: First boolean (Grasshopper A [item]).
        b: Second boolean (Grasshopper B [item]).
        c: Third boolean (Grasshopper C [item]).

    Outputs:
        result: Average value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Operators > Gate Majority (Vote).
        pyhopper decisions: none; true when at least two inputs are true, like Grasshopper.
    """

    display_name = "Gate Majority"
    nickname = "Vote"
    gh_guid = "78669f9c-4fea-44fd-ab12-2a69eeec58de"

    inputs = [
        InputParam("a", bool, Access.ITEM, default=False),
        InputParam("b", bool, Access.ITEM, default=False),
        InputParam("c", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("result", bool),
    ]

    def generate(self, a=False, b=False, c=False):
        return int(bool(a)) + int(bool(b)) + int(bool(c)) >= 2
