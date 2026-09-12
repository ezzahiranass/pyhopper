"""GateXor - Perform boolean exclusive disjunction (XOR gate) (Grasshopper "Gate Xor")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class GateXor(Component):
    """Perform boolean exclusive disjunction (XOR gate).

    Inputs:
        a: Left hand boolean (Grasshopper A [item]).
        b: Right hand boolean (Grasshopper B [item]).

    Outputs:
        result: Resulting value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Operators > Gate Xor (Xor).
        pyhopper decisions: both inputs are required, as in Grasshopper (unlike And / Or, a
        missing input does not collect and the gate emits nothing); exclusive disjunction of A and B.
    """

    display_name = "Gate Xor"
    nickname = "Xor"
    gh_guid = "de4a0d86-2709-4564-935a-88bf4d40af89"

    inputs = [
        InputParam("a", bool, Access.ITEM),
        InputParam("b", bool, Access.ITEM),
    ]
    outputs = [
        OutputParam("result", bool),
    ]

    def generate(self, a, b):
        return bool(a) != bool(b)
