"""SmallerThan - Smaller than (or equal to) (Grasshopper "Smaller Than")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class SmallerThan(Component):
    """Smaller than (or equal to).

    Inputs:
        first_number: Number to test (Grasshopper First Number [item]).
        second_number: Number to test against (Grasshopper Second Number [item]).

    Outputs:
        smaller_than: True if A < B (Grasshopper Smaller than).
        smaller_or_equal: True if A <= B (Grasshopper … or Equal to).

    Notes:
        Grasshopper: Maths > Operators > Smaller Than (Smaller).
        pyhopper decisions: outputs are ``smaller_than`` (<) and ``smaller_or_equal`` (<=).
    """

    display_name = "Smaller Than"
    nickname = "Smaller"
    gh_guid = "ae840986-cade-4e5a-96b0-570f007d4fc0"

    inputs = [
        InputParam("first_number", float, Access.ITEM, default=0.0),
        InputParam("second_number", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("smaller_than", bool),
        OutputParam("smaller_or_equal", bool),
    ]

    def generate(self, first_number=0.0, second_number=0.0):
        a, b = float(first_number), float(second_number)
        return a < b, a <= b
