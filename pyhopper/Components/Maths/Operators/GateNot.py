"""GateNot - Perform boolean negation (NOT gate) (Grasshopper "Gate Not")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class GateNot(Component):
    """Perform boolean negation (NOT gate).

    Inputs:
        a: Boolean value (Grasshopper A [item]).

    Outputs:
        result: Inverse of {A} (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Operators > Gate Not (Not).
        pyhopper decisions: none; behaviour matches Grasshopper.
    """

    display_name = "Gate Not"
    nickname = "Not"
    gh_guid = "cb2c7d3c-41b4-4c6d-a6bd-9235bd2851bb"

    inputs = [
        InputParam("a", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("result", bool),
    ]

    def generate(self, a=False):
        return not a
