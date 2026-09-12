"""ShortestList - Shrink a collection of lists to the shortest length amongst them (Grasshopper "Shortest List")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ShortestList(Component):
    """Shrink a collection of lists to the shortest length amongst them.

    Inputs:
        list_a: List (A) to operate on (Grasshopper List (A) [list]).
        list_b: List (B) to operate on (Grasshopper List (B) [list]).

    Outputs:
        list_a: Adjusted list (A) (Grasshopper List (A)).
        list_b: Adjusted list (B) (Grasshopper List (B)).

    Notes:
        Grasshopper: Sets > List > Shortest List (Short).
        pyhopper decisions: Grasshopper's default "Trim End" mode only: both lists are cut to the
        shorter length; a list that is not wired leaves the other one untouched (Grasshopper-verified).
    """

    display_name = "Shortest List"
    nickname = "Short"
    gh_guid = "5a13ec19-e4e9-43da-bf65-f93025fa87ca"

    inputs = [
        InputParam("list_a", None, Access.LIST, optional=True),
        InputParam("list_b", None, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("list_a", access=Access.LIST),
        OutputParam("list_b", access=Access.LIST),
    ]

    def generate(self, list_a=None, list_b=None):
        if list_a is None or list_b is None:
            # only one list wired: it passes through untouched, the other stays empty (Grasshopper-verified)
            return list(list_a or []), list(list_b or [])
        a, b = list(list_a), list(list_b)
        target = min(len(a), len(b))
        return a[:target], b[:target]
