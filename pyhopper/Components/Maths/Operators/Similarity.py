"""Similarity - Test for similarity of two numbers (Grasshopper "Similarity")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Similarity(Component):
    """Test for similarity of two numbers.

    Inputs:
        first_number: Number to compare (Grasshopper First Number [item]).
        second_number: Number to compare to (Grasshopper Second Number [item]).
        threshold: Percentage (0% ~ 100%) of A and B below which similarity is assumed (Grasshopper Threshold [item]).

    Outputs:
        similarity: True if A ≈ B (Grasshopper Similarity).
        absolute_difference: The absolute difference between A and B (Grasshopper Absolute difference).

    Notes:
        Grasshopper: Maths > Operators > Similarity (Similar).
        pyhopper decisions: Grasshopper-verified rule ``|A - B| <= T / 100 * max(|A|, |B|)``
        (the threshold is a percentage of the larger magnitude, inclusive; equal numbers are
        similar at any threshold). Default threshold 0.1 % as in Grasshopper.
    """

    display_name = "Similarity"
    nickname = "Similar"
    gh_guid = "40177d8a-a35c-4622-bca7-d150031fe427"

    inputs = [
        InputParam("first_number", float, Access.ITEM, default=0.0),
        InputParam("second_number", float, Access.ITEM, default=0.0),
        InputParam("threshold", float, Access.ITEM, default=0.1),
    ]
    outputs = [
        OutputParam("similarity", bool),
        OutputParam("absolute_difference", float),
    ]

    def generate(self, first_number=0.0, second_number=0.0, threshold=0.1):
        a, b = float(first_number), float(second_number)
        difference = abs(a - b)
        allowance = float(threshold) / 100.0 * max(abs(a), abs(b))
        return difference <= allowance, difference
