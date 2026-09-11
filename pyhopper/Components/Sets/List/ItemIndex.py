"""ItemIndex - Retrieve the index of a certain item in a list (Grasshopper "Item Index")."""

from __future__ import annotations

import builtins

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Items import index_of


class ItemIndex(Component):
    """Retrieve the index of a certain item in a list.

    Inputs:
        list: List to search (Grasshopper List [list]).
        item: Item to search for (Grasshopper Item [item]).

    Outputs:
        index: The index of item in the list, or -1 if the item could not be found. (Grasshopper Index).

    Notes:
        Grasshopper: Sets > List > Item Index (Index).
        pyhopper decisions: items are compared by type and value (``Utils/Items.item_key``), so ``2`` is
        found among numbers; Grasshopper compares object references and returns ``-1``
        for most inputs. Missing items give ``-1``.
    """

    display_name = "Item Index"
    nickname = "Index"
    gh_guid = "a759fd55-e6be-4673-8365-c28d5b52c6c0"

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("item", None, Access.ITEM),
    ]
    outputs = [
        OutputParam("index", int),
    ]

    def generate(self, list=None, item=None):
        return index_of(builtins.list(list or []), item)
