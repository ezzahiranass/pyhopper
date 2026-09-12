"""OneOverX - Compute one over x (Grasshopper "One Over X")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class OneOverX(Component):
    """Compute one over x.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > One Over X (1/x).
        pyhopper decisions: zero raises ``ValueError`` (Grasshopper emits Infinity with a
        "Division by zero" warning).
    """

    display_name = "One Over X"
    nickname = "1/x"
    gh_guid = "797d922f-3a1d-46fe-9155-358b009b5997"

    inputs = [
        InputParam("value", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=1.0):
        x = float(value)
        if x == 0.0:
            raise ValueError("OneOverX cannot divide by zero")
        return 1.0 / x
