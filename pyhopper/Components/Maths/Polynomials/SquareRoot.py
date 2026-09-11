"""SquareRoot - Compute the square root of a value (Grasshopper "Square Root")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class SquareRoot(Component):
    """Compute the square root of a value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > Square Root (Sqrt).
        pyhopper decisions: negative values raise ``ValueError`` (Grasshopper returns a complex number).
    """

    display_name = "Square Root"
    nickname = "Sqrt"
    gh_guid = "ad476cb7-b6d1-41c8-986b-0df243a64146"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        x = float(value)
        if x < 0.0:
            raise ValueError("SquareRoot requires a non-negative value")
        return math.sqrt(x)
