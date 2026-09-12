"""LongestList - Grow a collection of lists to the longest length amongst them (Grasshopper "Longest List")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from .._lists import extend_last


class LongestList(Component):
    """Grow a collection of lists to the longest length amongst them.

    Inputs:
        list_a: List (A) to operate on (Grasshopper List (A) [list]).
        list_b: List (B) to operate on (Grasshopper List (B) [list]).

    Outputs:
        list_a: Adjusted list (A) (Grasshopper List (A)).
        list_b: Adjusted list (B) (Grasshopper List (B)).

    Notes:
        Grasshopper: Sets > List > Longest List (Long).
        pyhopper decisions: Grasshopper's default "Repeat Last" mode only (the other modes are
        right-click options): the shorter list repeats its last item until both are the same length;
        a missing list stays empty.
    """

    display_name = "Longest List"
    nickname = "Long"
    gh_guid = "8440fd1b-b6e0-4bdb-aa93-4ec295c213e9"

    inputs = [
        InputParam("list_a", None, Access.LIST, optional=True),
        InputParam("list_b", None, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("list_a", access=Access.LIST),
        OutputParam("list_b", access=Access.LIST),
    ]

    def generate(self, list_a=None, list_b=None):
        a, b = list(list_a or []), list(list_b or [])
        target = max(len(a), len(b))
        return extend_last(a, target), extend_last(b, target)
