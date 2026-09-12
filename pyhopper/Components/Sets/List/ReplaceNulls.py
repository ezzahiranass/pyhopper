"""ReplaceNulls - Replace nulls or invalid data with other data (Grasshopper "Replace Nulls")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ReplaceNulls(Component):
    """Replace nulls or invalid data with other data.

    Inputs:
        items: Items to test for null (Grasshopper Items [list]).
        replacements: Items to replace nulls with (Grasshopper Replacements [list]).

    Outputs:
        result: List without any nulls (Grasshopper Items).
        count: Number of items replaced (Grasshopper Count).

    Notes:
        Grasshopper: Sets > List > Replace Nulls (NullRep).
        pyhopper decisions: the n-th null takes the n-th replacement, the last replacement
        repeating once they run out (Grasshopper-verified); ``count`` is the number of nulls
        replaced. Nulls with no replacements at all raise ``ValueError`` where Grasshopper throws.
    """

    display_name = "Replace Nulls"
    nickname = "NullRep"
    gh_guid = "f3230ecb-3631-4d6f-86f2-ef4b2ed37f45"

    inputs = [
        InputParam("items", None, Access.LIST),
        InputParam("replacements", None, Access.LIST),
    ]
    outputs = [
        OutputParam("result", access=Access.LIST),
        OutputParam("count", int),
    ]

    def generate(self, items=None, replacements=None):
        values = list(items or [])
        pool = list(replacements or [])
        replaced = 0
        for position, item in enumerate(values):
            if item is None:
                if not pool:
                    raise ValueError("ReplaceNulls has nulls to replace but no replacements")
                values[position] = pool[min(replaced, len(pool) - 1)]
                replaced += 1
        return values, replaced
