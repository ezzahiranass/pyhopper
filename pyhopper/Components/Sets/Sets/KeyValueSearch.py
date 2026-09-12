"""KeyValueSearch - Extract an item from a collection using a key-value match (Grasshopper "Key/Value Search")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Items import item_key


class KeyValueSearch(Component):
    """Extract an item from a collection using a key-value match.

    Inputs:
        keys: A list of key values. (Grasshopper Keys [list]).
        values: A list of value data, one for each key. (Grasshopper Values [list]).
        search: A key value to search for (Grasshopper Search [item]).

    Outputs:
        result: Resulting item in the value list that matches the Search key (Grasshopper Result).

    Notes:
        Grasshopper: Sets > Sets > Key/Value Search (KeySearch).
        pyhopper decisions: Grasshopper-verified — the value paired with the first key equal (by type
        and value) to ``search``; a missing key emits nothing (Grasshopper warns), unequal key and
        value counts raise ``ValueError``.
    """

    display_name = "Key/Value Search"
    nickname = "KeySearch"
    gh_guid = "1edcc3cf-cf84-41d4-8204-561162cfe510"

    inputs = [
        InputParam("keys", None, Access.LIST),
        InputParam("values", None, Access.LIST),
        InputParam("search", None, Access.ITEM),
    ]
    outputs = [
        OutputParam("result"),
    ]

    def generate(self, keys=None, values=None, search=None):
        key_list, value_list = list(keys or []), list(values or [])
        if len(key_list) != len(value_list):
            raise ValueError("KeyValueSearch needs as many keys as values")
        wanted = item_key(search)
        for key, value in zip(key_list, value_list):
            if item_key(key) == wanted:
                return value
        return Component.NO_OUTPUT
