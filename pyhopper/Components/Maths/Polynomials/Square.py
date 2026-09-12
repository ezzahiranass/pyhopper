"""Square - Compute the square of a value (Grasshopper "Square")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Square(Component):
    """Compute the square of a value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > Square (Sqr).
        pyhopper decisions: none; behaviour matches Grasshopper.
    """

    display_name = "Square"
    nickname = "Sqr"
    gh_guid = "2280dde4-9fa2-4b4a-ae2f-37d554861367"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        x = float(value)
        return x * x
