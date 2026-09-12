"""Secant - Compute the secant (reciprocal of the Cosine) of an angle (Grasshopper "Secant")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Secant(Component):
    """Compute the secant (reciprocal of the Cosine) of an angle.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Trig > Secant (Sec).
        pyhopper decisions: ``1 / math.cos(x)`` in radians; an exactly zero cosine raises
        ``ValueError`` (Grasshopper emits the largest double there); like Grasshopper, near-singular
        angles such as pi/2 simply give huge values.
    """

    display_name = "Secant"
    nickname = "Sec"
    gh_guid = "60103def-1bb7-4700-b294-3a89100525c4"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        divisor = math.cos(float(value))
        if divisor == 0.0:
            raise ValueError("Secant is undefined where the cosine is zero")
        return 1.0 / divisor
