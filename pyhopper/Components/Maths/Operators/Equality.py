"""Equality - Test for (in)equality of two numbers (Grasshopper "Equality")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Equality(Component):
    """Test for (in)equality of two numbers.

    Inputs:
        first_number: Number to compare (Grasshopper First Number [item]).
        second_number: Number to compare to (Grasshopper Second Number [item]).

    Outputs:
        equality: True if A = B (Grasshopper Equality).
        inequality: True if A ≠ B (Grasshopper Inequality).

    Notes:
        Grasshopper: Maths > Operators > Equality (Equals).
        pyhopper decisions: exact floating-point comparison, like Grasshopper.
    """

    display_name = "Equality"
    nickname = "Equals"
    gh_guid = "5db0fb89-4f22-4f09-a777-fa5e55aed7ec"

    inputs = [
        InputParam("first_number", float, Access.ITEM, default=0.0),
        InputParam("second_number", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("equality", bool),
        OutputParam("inequality", bool),
    ]

    def generate(self, first_number=0.0, second_number=0.0):
        equal = float(first_number) == float(second_number)
        return equal, not equal
