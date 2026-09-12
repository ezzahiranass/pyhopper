"""ReplaceMembers - Replace members in a set (Grasshopper "Replace Members")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Items import item_key


class ReplaceMembers(Component):
    """Replace members in a set.

    Inputs:
        set: Set to operate on. (Grasshopper Set [list]).
        find: Item(s) to replace. (Grasshopper Find [list]).
        replace: Item(s) to replace with. (Grasshopper Replace [list]).

    Outputs:
        result: Sets with replaced members. (Grasshopper Result).

    Notes:
        Grasshopper: Sets > Sets > Replace Members (Replace).
        pyhopper decisions: Grasshopper-verified — every occurrence of ``find[i]`` becomes
        ``replace[i]``; with no replacements the found members are removed; any other mismatch between
        the two counts raises ``ValueError`` (Grasshopper reports an error and emits nothing);
        matching is by type and value.
    """

    display_name = "Replace Members"
    nickname = "Replace"
    gh_guid = "bafac914-ede4-4a59-a7b2-cc41bc3de961"

    inputs = [
        InputParam("set", None, Access.LIST),
        InputParam("find", None, Access.LIST),
        InputParam("replace", None, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("result", access=Access.LIST),
    ]

    def generate(self, set=None, find=None, replace=None):
        finds, replacements = list(find or []), list(replace or [])
        if replacements and len(replacements) != len(finds):
            raise ValueError("ReplaceMembers needs as many replacements as items to find")
        table = {item_key(item): index for index, item in enumerate(finds)}
        result = []
        for item in (set or []):
            index = table.get(item_key(item))
            if index is None:
                result.append(item)
            elif replacements:
                result.append(replacements[index])
        return result
