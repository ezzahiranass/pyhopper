"""GateXnor - Perform boolean biconditional (XNOR gate) (Grasshopper "Gate Xnor")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class GateXnor(Component):
    """Perform boolean biconditional (XNOR gate).

    Inputs:
        a: Left hand boolean (Grasshopper A [item]).
        b: Right hand boolean (Grasshopper B [item]).

    Outputs:
        result: Resulting value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Operators > Gate Xnor (Xnor).
        pyhopper decisions: none; ``a == b`` like Grasshopper.
    """

    display_name = "Gate Xnor"
    nickname = "Xnor"
    gh_guid = "b6aedcac-bf43-42d4-899e-d763612f834d"

    inputs = [
        InputParam("a", bool, Access.ITEM, default=False),
        InputParam("b", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("result", bool),
    ]

    def generate(self, a=False, b=False):
        return bool(a) == bool(b)
