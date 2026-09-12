"""Average - Solve the arithmetic average for a set of items (Grasshopper "Average")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._arith import mean


class Average(Component):
    """Solve the arithmetic average for a set of items.

    Inputs:
        input: Input values for averaging (Grasshopper Input [list]).

    Outputs:
        arithmetic_mean: Arithmetic mean (average) of all input values (Grasshopper Arithmetic mean).

    Notes:
        Grasshopper: Maths > Util > Average (Avr).
        pyhopper decisions: numbers, vectors and points are averaged; an empty branch stays an empty
        branch (Grasshopper emits a null); mixed kinds raise ``TypeError``.
    """

    display_name = "Average"
    nickname = "Avr"
    gh_guid = "7986486c-621a-48fb-8f27-a28a22c91cc9"

    inputs = [
        InputParam("input", None, Access.LIST),
    ]
    outputs = [
        OutputParam("arithmetic_mean"),
    ]

    def generate(self, input=None):
        items = list(input or [])
        if not items:
            return Component.NO_OUTPUT
        return mean(items, "Average")
