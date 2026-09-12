"""CoSecant - Compute the co-secant (reciprocal of the Sine) of an angle (Grasshopper "CoSecant")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class CoSecant(Component):
    """Compute the co-secant (reciprocal of the Sine) of an angle.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Trig > CoSecant (Csc).
        pyhopper decisions: ``1 / math.sin(x)`` in radians; an exactly zero sine raises
        ``ValueError`` (Grasshopper emits the largest double there); like Grasshopper, near-singular
        angles such as pi/2 simply give huge values. Default 1 (Grasshopper has none; 0 is singular).
    """

    display_name = "CoSecant"
    nickname = "Csc"
    gh_guid = "d222500b-dfd5-45e0-933e-eabefd07cbfa"

    inputs = [
        InputParam("value", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=1.0):
        divisor = math.sin(float(value))
        if divisor == 0.0:
            raise ValueError("CoSecant is undefined where the sine is zero")
        return 1.0 / divisor
