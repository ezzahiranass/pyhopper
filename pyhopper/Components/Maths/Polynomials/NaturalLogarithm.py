"""NaturalLogarithm - Compute the natural logarithm of a value (Grasshopper "Natural logarithm")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class NaturalLogarithm(Component):
    """Compute the natural logarithm of a value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > Natural logarithm (Ln).
        pyhopper decisions: zero and negative values raise ``ValueError`` (Grasshopper emits -Infinity
        and NaN).
    """

    display_name = "Natural logarithm"
    nickname = "Ln"
    gh_guid = "23afc7aa-2d2f-4ae7-b876-bf366246b826"

    inputs = [
        InputParam("value", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=1.0):
        x = float(value)
        if x <= 0.0:
            raise ValueError("NaturalLogarithm requires a positive value")
        return math.log(x)
