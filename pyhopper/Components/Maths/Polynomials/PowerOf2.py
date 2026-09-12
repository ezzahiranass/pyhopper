"""PowerOf2 - Raise 2 to the power of N (Grasshopper "Power of 2")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class PowerOf2(Component):
    """Raise 2 to the power of N.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > Power of 2 (2º).
        pyhopper decisions: none; behaviour matches Grasshopper (``2 ** x`` for any real x).
    """

    display_name = "Power of 2"
    nickname = "2º"
    gh_guid = "7a1e5fd7-b7da-4244-a261-f1da66614992"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        return 2.0 ** float(value)
