"""MassMultiplication - Perform mass multiplication of a list of items (Grasshopper "Mass Multiplication")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._arith import multiply


class MassMultiplication(Component):
    """Perform mass multiplication of a list of items.

    Inputs:
        input: Input values for mass multiplication. (Grasshopper Input [list]).

    Outputs:
        result: Result of mass multiplication (Grasshopper Result).
        partial_results: List of partial results (Grasshopper Partial Results).

    Notes:
        Grasshopper: Maths > Operators > Mass Multiplication (MM).
        pyhopper decisions: mirrors Mass Addition — numbers multiply, a number scales a vector or
        point, vector times vector is the dot product and point times point is component-wise
        (all Grasshopper-verified); text raises ``TypeError`` (Grasshopper: "not supported"); an
        empty branch stays empty on both outputs where Grasshopper emits a null result.
    """

    display_name = "Mass Multiplication"
    nickname = "MM"
    gh_guid = "e44c1bd7-72cc-4697-80c9-02787baf7bb4"

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
            partials.append(multiply(partials[-1], item, "MassMultiplication"))
        return partials[-1], partials
