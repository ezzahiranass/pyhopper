"""Sinc - Compute the sinc (Sinus Cardinalis) of a value (Grasshopper "Sinc")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Sinc(Component):
    """Compute the sinc (Sinus Cardinalis) of a value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Trig > Sinc (Sinc).
        pyhopper decisions: the unnormalised ``sin(x) / x`` with ``sinc(0) = 1``, like Grasshopper.
    """

    display_name = "Sinc"
    nickname = "Sinc"
    gh_guid = "a2d9503d-a83c-4d71-81e0-02af8d09cd0c"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        x = float(value)
        return 1.0 if x == 0.0 else math.sin(x) / x
