"""PowerOfE - Raise E to the power of N (Grasshopper "Power of E")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math


class PowerOfE(Component):
    """Raise E to the power of N.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > Power of E (Eº).
        pyhopper decisions: none; behaviour matches Grasshopper (``e ** x``).
    """

    display_name = "Power of E"
    nickname = "Eº"
    gh_guid = "c717f26f-e4a0-475c-8e1c-b8f77af1bc99"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        return math.exp(float(value))
