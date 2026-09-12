"""ArcTangent - Compute the angle whose tangent is the specified value (Grasshopper "ArcTangent")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math


class ArcTangent(Component):
    """Compute the angle whose tangent is the specified value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Trig > ArcTangent (ATan).
        pyhopper decisions: result in radians; behaviour matches Grasshopper.
    """

    display_name = "ArcTangent"
    nickname = "ATan"
    gh_guid = "b4647919-d041-419e-99f5-fa0dc0ddb8b6"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        return math.atan(float(value))
