"""Cosine - Compute the cosine of a value (Grasshopper "Cosine")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Cosine(Component):
    """Compute the cosine of a value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Trig > Cosine (Cos).
        pyhopper decisions: angles are in radians.
    """

    display_name = "Cosine"
    nickname = "Cos"
    gh_guid = "d2d2a900-780c-4d58-9a35-1f9d8d35df6f"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        return math.cos(float(value))
