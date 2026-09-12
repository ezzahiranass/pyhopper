"""RelativeItem - Retrieve a relative item combo from a data tree (Grasshopper "Relative Item")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree

from ._relative import relative_items


class RelativeItem(Component):
    """Retrieve a relative item combo from a data tree.

    Inputs:
        tree: Tree to operate on (Grasshopper Tree [tree]).
        offset: Relative offset for item combo (Grasshopper Offset [item]).
        wrap_paths: Wrap paths when the shift is out of bounds (Grasshopper Wrap Paths [item]).
        wrap_items: Wrap items when the shift is out of bounds (Grasshopper Wrap Items [item]).

    Outputs:
        item_a: Tree item (Grasshopper Item A).
        item_b: Tree item relative to A (Grasshopper Item B).

    Notes:
        Grasshopper: Sets > Tree > Relative Item (RelItem).
        pyhopper decisions: Grasshopper-verified — the offset ``{0;+1}[+1]`` names a path offset and
        an optional item offset; every branch pairs its items with the items of the branch that many
        steps away (item ``i`` with item ``i + offset``), keeping only pairs that exist unless the
        wraps are on: wrapped paths cycle through the indices that exist among the paths sharing their
        prefix, wrapped items cycle within the branch. Both outputs sit at the source branch's path;
        branches without pairs vanish. An offset without a ``{…}`` block raises ``ValueError``.
    """

    display_name = "Relative Item"
    nickname = "RelItem"
    gh_guid = "fac0d5be-e3ff-4bbb-9742-ec9a54900d41"

    inputs = [
        InputParam("tree", None, Access.TREE),
        InputParam("offset", str, Access.ITEM, default=""),
        InputParam("wrap_paths", bool, Access.ITEM, default=False),
        InputParam("wrap_items", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("item_a", access=Access.TREE),
        OutputParam("item_b", access=Access.TREE),
    ]

    def generate(self, tree=None, offset="", wrap_paths=False, wrap_items=False):
        return relative_items(tree if tree is not None else DataTree(), None, offset, bool(wrap_paths), bool(wrap_items))
