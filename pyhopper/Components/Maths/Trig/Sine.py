"""Sine - Compute the sine of a value (Grasshopper "Sine")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Sine(Component):
    """Compute the sine of a value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Trig > Sine (Sin).
        pyhopper decisions: angles are in radians.
    """

    display_name = "Sine"
    nickname = "Sin"
    gh_guid = "7663efbb-d9b8-4c6a-a0da-c3750a7bbe77"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        return math.sin(float(value))
