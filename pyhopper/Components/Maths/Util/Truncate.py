"""Truncate - Perform truncation of numerical extremes (Grasshopper "Truncate")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._arith import is_number


class Truncate(Component):
    """Perform truncation of numerical extremes.

    Inputs:
        input: Input values for truncation (Grasshopper Input [list]).
        truncation_factor: Truncation factor. Must be between 0.0 (no trucation) and 1.0 (full truncation) (Grasshopper Truncation factor [item]).

    Outputs:
        result: Truncated set (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Util > Truncate (Trunc).
        pyhopper decisions: Grasshopper-verified — the list is sorted ascending and
        ``round_half_even(n * t / 2)`` items are dropped from each end (a factor below 0 drops
        nothing, 1 or more drops everything); the result stays sorted. Only numbers (bools count
        as numbers) are accepted; anything else raises ``TypeError``.
    """

    display_name = "Truncate"
    nickname = "Trunc"
    gh_guid = "bd96f893-d57b-4f04-90d0-dca0d72ff2f9"

    inputs = [
        InputParam("input", None, Access.LIST),
        InputParam("truncation_factor", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", access=Access.LIST),
    ]

    def generate(self, input=None, truncation_factor=0.0):
        items = list(input or [])
        if not all(is_number(item) or isinstance(item, bool) for item in items):
            raise TypeError("Truncate requires a list of numbers")
        ordered = sorted(items, key=float)
        per_end = max(0, round(len(ordered) * min(max(float(truncation_factor), 0.0), 1.0) / 2.0))
        return ordered[per_end: len(ordered) - per_end] if per_end < len(ordered) - per_end else []
