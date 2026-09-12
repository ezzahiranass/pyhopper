"""GateNor - Perform boolean joint denial (NOR gate) (Grasshopper "Gate Nor")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class GateNor(Component):
    """Perform boolean joint denial (NOR gate).

    Inputs:
        a: Left hand boolean (Grasshopper A [item]).
        b: Right hand boolean (Grasshopper B [item]).

    Outputs:
        result: Resulting value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Operators > Gate Nor (Nor).
        pyhopper decisions: both inputs are required, as in Grasshopper (unlike And / Or, a
        missing input does not collect and the gate emits nothing); joint denial of A and B.
    """

    display_name = "Gate Nor"
    nickname = "Nor"
    gh_guid = "548177c2-d1db-4172-b667-bec979e2d38b"

    inputs = [
        InputParam("a", bool, Access.ITEM),
        InputParam("b", bool, Access.ITEM),
    ]
    outputs = [
        OutputParam("result", bool),
    ]

    def generate(self, a, b):
        return not (bool(a) or bool(b))
