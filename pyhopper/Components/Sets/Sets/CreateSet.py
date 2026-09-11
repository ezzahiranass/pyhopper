"""CreateSet - Creates the valid set from a list of items (a valid set only contains distinct elements) (Grasshopper "Create Set")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Items import item_key


class CreateSet(Component):
    """Creates the valid set from a list of items (a valid set only contains distinct elements).

    Inputs:
        list: List of data. (Grasshopper List [list]).

    Outputs:
        set: A set of all the distincts values in L (Grasshopper Set).
        map: An index map from original indices to set indices (Grasshopper Map).

    Notes:
        Grasshopper: Sets > Sets > Create Set (CSet).
        pyhopper decisions: members are unique by type and value (``1``, ``1.0``, ``True`` and ``"1"`` are
        four members, like Grasshopper) and keep first-appearance order; ``map`` gives
        each input item's index in the set.
    """

    display_name = "Create Set"
    nickname = "CSet"
    gh_guid = "98c3c63a-e78a-43ea-a111-514fcf312c95"

    inputs = [
        InputParam("list", None, Access.LIST),
    ]
    outputs = [
        OutputParam("set", access=Access.LIST),
        OutputParam("map", int, access=Access.LIST),
    ]

    def generate(self, list=None):
        members = []
        positions = {}
        mapping = []
        for item in list or []:
            key = item_key(item)
            if key not in positions:
                positions[key] = len(members)
                members.append(item)
            mapping.append(positions[key])
        return members, mapping
