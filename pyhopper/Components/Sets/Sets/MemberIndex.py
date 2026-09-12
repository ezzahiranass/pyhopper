"""MemberIndex - Find the occurences of a specific member in a set (Grasshopper "Member Index")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Items import indices_of


class MemberIndex(Component):
    """Find the occurences of a specific member in a set.

    Inputs:
        set: Set to operate on. (Grasshopper Set [list]).
        member: Member to search for. (Grasshopper Member [item]).

    Outputs:
        index: Indices of member. (Grasshopper Index).
        count: Number of occurences of the member. (Grasshopper Count).

    Notes:
        Grasshopper: Sets > Sets > Member Index (MIndex).
        pyhopper decisions: members are compared by type and value (``2`` does not match ``2.0``, like
        Grasshopper); a missing member gives an empty index list and a count of 0.
    """

    display_name = "Member Index"
    nickname = "MIndex"
    gh_guid = "3ff27857-b988-417a-b495-b24c733dbd00"

    inputs = [
        InputParam("set", None, Access.LIST),
        InputParam("member", None, Access.ITEM),
    ]
    outputs = [
        OutputParam("index", int, access=Access.LIST),
        OutputParam("count", int),
    ]

    def generate(self, set=None, member=None):
        found = indices_of(builtins.list(set or []), member)
        return found, len(found)
