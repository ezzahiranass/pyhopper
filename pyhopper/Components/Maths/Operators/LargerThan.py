"""LargerThan - Larger than (or equal to) (Grasshopper "Larger Than")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class LargerThan(Component):
    """Larger than (or equal to).

    Inputs:
        first_number: Number to test (Grasshopper First Number [item]).
        second_number: Number to test against (Grasshopper Second Number [item]).

    Outputs:
        larger_than: True if A > B (Grasshopper Larger than).
        larger_or_equal: True if A >= B (Grasshopper … or Equal to).

    Notes:
        Grasshopper: Maths > Operators > Larger Than (Larger).
        pyhopper decisions: outputs are ``larger_than`` (>) and ``larger_or_equal`` (>=).
    """

    display_name = "Larger Than"
    nickname = "Larger"
    gh_guid = "30d58600-1aab-42db-80a3-f1ea6c4269a0"

    inputs = [
        InputParam("first_number", float, Access.ITEM, default=0.0),
        InputParam("second_number", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("larger_than", bool),
        OutputParam("larger_or_equal", bool),
    ]

    def generate(self, first_number=0.0, second_number=0.0):
        a, b = float(first_number), float(second_number)
        return a > b, a >= b
