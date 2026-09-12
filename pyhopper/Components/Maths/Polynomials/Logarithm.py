"""Logarithm - Compute the Base-10 logarithm of a value (Grasshopper "Logarithm")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math


class Logarithm(Component):
    """Compute the Base-10 logarithm of a value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > Logarithm (Log).
        pyhopper decisions: base-10 logarithm; zero and negative values raise ``ValueError``
        (Grasshopper emits -Infinity and NaN).
    """

    display_name = "Logarithm"
    nickname = "Log"
    gh_guid = "27d6f724-a701-4585-992f-3897488abf08"

    inputs = [
        InputParam("value", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=1.0):
        x = float(value)
        if x <= 0.0:
            raise ValueError("Logarithm requires a positive value")
        return math.log10(x)
