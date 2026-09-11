"""GateAnd - Perform boolean conjunction (AND gate) (Grasshopper "Gate And")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class GateAnd(Component):
    """Perform boolean conjunction (AND gate).

    Inputs:
        a: First boolean for AND operation (Grasshopper A [item]).
        b: Second boolean for AND operation (Grasshopper B [item]).

    Outputs:
        result: Resulting value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Operators > Gate And (And).
        pyhopper decisions: like Grasshopper, a missing input is ignored (the conjunction of
        the values that are present); with neither input the component emits nothing
        where Grasshopper emits a null.
    """

    display_name = "Gate And"
    nickname = "And"
    gh_guid = "040f195d-0b4e-4fe0-901f-fedb2fd3db15"

    inputs = [
        InputParam("a", bool, Access.ITEM, optional=True),
        InputParam("b", bool, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("result", bool),
    ]

    def generate(self, a=None, b=None):
        present = [bool(value) for value in (a, b) if value is not None]
        if not present:
            return Component.NO_OUTPUT
        return all(present)
