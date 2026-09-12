"""CoTangent - Compute the co-tangent (reciprocal of the Tangent) of an angle (Grasshopper "CoTangent")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class CoTangent(Component):
    """Compute the co-tangent (reciprocal of the Tangent) of an angle.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Trig > CoTangent (Cot).
        pyhopper decisions: ``1 / math.tan(x)`` in radians; an exactly zero tangent raises
        ``ValueError`` (Grasshopper emits the largest double there); like Grasshopper, near-singular
        angles such as pi/2 simply give huge values. Default 1 (Grasshopper has none; 0 is singular).
    """

    display_name = "CoTangent"
    nickname = "Cot"
    gh_guid = "1f602c33-f38e-4f47-898b-359f0a4de3c2"

    inputs = [
        InputParam("value", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=1.0):
        divisor = math.tan(float(value))
        if divisor == 0.0:
            raise ValueError("CoTangent is undefined where the tangent is zero")
        return 1.0 / divisor
