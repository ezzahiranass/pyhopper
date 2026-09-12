"""FindSimilarMember - Find the most similar member in a set (Grasshopper "Find similar member")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._similarity import similarity_score


class FindSimilarMember(Component):
    """Find the most similar member in a set.

    Inputs:
        data: Data to search for. (Grasshopper Data [item]).
        set: Set to search. (Grasshopper Set [list]).

    Outputs:
        hit: Member in S closest to D. (Grasshopper Hit).
        index: Index of H in set. (Grasshopper Index).

    Notes:
        Grasshopper: Sets > Sets > Find similar member (FSim).
        pyhopper decisions: Grasshopper-verified — numbers are compared by absolute difference,
        points by distance and everything else (text, booleans, vectors, mixed kinds) by the edit
        distance of their text forms; ties go to the lowest index; an empty set emits nothing.
    """

    display_name = "Find similar member"
    nickname = "FSim"
    gh_guid = "b4d4235f-14ff-4d4e-a29a-b358dcd2baf4"

    inputs = [
        InputParam("data", None, Access.ITEM),
        InputParam("set", None, Access.LIST),
    ]
    outputs = [
        OutputParam("hit"),
        OutputParam("index", int),
    ]

    def generate(self, data=None, set=None):
        members = list(set or [])
        if not members:
            return Component.NO_OUTPUT, Component.NO_OUTPUT
        scores = [similarity_score(data, member) for member in members]
        index = min(range(len(members)), key=lambda position: (scores[position], position))
        return members[index], index
