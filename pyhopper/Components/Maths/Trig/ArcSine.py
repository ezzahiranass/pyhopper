"""ArcSine - Compute the angle whose sine is the specified value (Grasshopper "ArcSine")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math


class ArcSine(Component):
    """Compute the angle whose sine is the specified value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Trig > ArcSine (ASin).
        pyhopper decisions: result in radians; values outside [-1, 1] raise ``ValueError``
        (Grasshopper emits NaN).
    """

    display_name = "ArcSine"
    nickname = "ASin"
    gh_guid = "cc15ba56-fae7-4f05-b599-cb7c43b60e11"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        x = float(value)
        if x < -1.0 or x > 1.0:
            raise ValueError("ArcSine requires a value in [-1, 1]")
        return math.asin(x)
