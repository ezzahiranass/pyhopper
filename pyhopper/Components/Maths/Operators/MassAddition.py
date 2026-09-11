"""MassAddition - Perform mass addition of a list of items (Grasshopper "Mass Addition")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._arith import add


class MassAddition(Component):
    """Perform mass addition of a list of items.

    Inputs:
        input: Input values for mass addition. (Grasshopper Input [list]).

    Outputs:
        result: Result of mass addition (Grasshopper Result).
        partial_results: List of partial results (Grasshopper Partial Results).

    Notes:
        Grasshopper: Maths > Operators > Mass Addition (MA).
        pyhopper decisions: works on numbers, text (concatenation), vectors and points (Grasshopper
        rejects text); an empty branch stays an empty branch on both outputs where Grasshopper emits
        a null result; mixed item kinds raise ``TypeError`` (Grasshopper stops at the first bad item).
    """

    display_name = "Mass Addition"
    nickname = "MA"
    gh_guid = "5b850221-b527-4bd6-8c62-e94168cd6efa"

    inputs = [
        InputParam("input", None, Access.LIST),
    ]
    outputs = [
        OutputParam("result"),
        OutputParam("partial_results", access=Access.LIST),
    ]

    def generate(self, input=None):
        items = list(input or [])
        if not items:
            return Component.NO_OUTPUT, []
        partials = [items[0]]
        for item in items[1:]:
            partials.append(add(partials[-1], item, "MassAddition"))
        return partials[-1], partials
