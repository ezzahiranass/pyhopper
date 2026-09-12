"""ArcCosine - Compute the angle whose cosine is the specified value (Grasshopper "ArcCosine")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math


class ArcCosine(Component):
    """Compute the angle whose cosine is the specified value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Trig > ArcCosine (ACos).
        pyhopper decisions: result in radians; values outside [-1, 1] raise ``ValueError``
        (Grasshopper emits NaN).
    """

    display_name = "ArcCosine"
    nickname = "ACos"
    gh_guid = "49584390-d541-41f7-b5f6-1f9515ac0f73"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        x = float(value)
        if x < -1.0 or x > 1.0:
            raise ValueError("ArcCosine requires a value in [-1, 1]")
        return math.acos(x)
