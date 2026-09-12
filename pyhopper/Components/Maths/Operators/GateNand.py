"""GateNand - Perform boolean alternative denial (NAND gate) (Grasshopper "Gate Nand")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class GateNand(Component):
    """Perform boolean alternative denial (NAND gate).

    Inputs:
        a: Left hand boolean (Grasshopper A [item]).
        b: Right hand boolean (Grasshopper B [item]).

    Outputs:
        result: Resulting value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Operators > Gate Nand (Nand).
        pyhopper decisions: both inputs are required, as in Grasshopper (unlike And / Or, a
        missing input does not collect and the gate emits nothing); alternative denial of A and B.
    """

    display_name = "Gate Nand"
    nickname = "Nand"
    gh_guid = "5ca5de6b-bc71-46c4-a8f7-7f30d7040acb"

    inputs = [
        InputParam("a", bool, Access.ITEM),
        InputParam("b", bool, Access.ITEM),
    ]
    outputs = [
        OutputParam("result", bool),
    ]

    def generate(self, a, b):
        return not (bool(a) and bool(b))
