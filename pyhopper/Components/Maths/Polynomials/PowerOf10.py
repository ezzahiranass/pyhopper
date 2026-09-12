"""PowerOf10 - Raise 10 to the power of N (Grasshopper "Power of 10")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class PowerOf10(Component):
    """Raise 10 to the power of N.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > Power of 10 (10º).
        pyhopper decisions: none; behaviour matches Grasshopper (``10 ** x`` for any real x).
    """

    display_name = "Power of 10"
    nickname = "10º"
    gh_guid = "2ebb82ef-1f90-4ac9-9a71-1fe0f4ef7044"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        return 10.0 ** float(value)
