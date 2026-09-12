"""Tangent - Compute the tangent of a value (Grasshopper "Tangent")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Tangent(Component):
    """Compute the tangent of a value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Trig > Tangent (Tan).
        pyhopper decisions: angles are in radians; poles return the large finite value ``math.tan`` produces.
    """

    display_name = "Tangent"
    nickname = "Tan"
    gh_guid = "0f31784f-7177-4104-8500-1f4f4a306df4"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        return math.tan(float(value))
