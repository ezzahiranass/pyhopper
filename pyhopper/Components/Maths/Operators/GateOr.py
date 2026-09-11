"""GateOr - Perform boolean disjunction (OR gate) (Grasshopper "Gate Or")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class GateOr(Component):
    """Perform boolean disjunction (OR gate).

    Inputs:
        a: First boolean for OR operation (Grasshopper A [item]).
        b: Second boolean for OR operation (Grasshopper B [item]).

    Outputs:
        result: Resulting value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Operators > Gate Or (Or).
        pyhopper decisions: like Grasshopper, a missing input is ignored (the disjunction of
        the values that are present); with neither input the component emits nothing
        where Grasshopper emits a null.
    """

    display_name = "Gate Or"
    nickname = "Or"
    gh_guid = "5cad70f9-5a53-4c5c-a782-54a479b4abe3"

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
        return any(present)
