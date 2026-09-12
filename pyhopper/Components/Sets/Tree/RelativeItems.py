"""RelativeItems - Retrieve a relative item combo from two data trees (Grasshopper "Relative Items")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree

from ._relative import relative_items


class RelativeItems(Component):
    """Retrieve a relative item combo from two data trees.

    Inputs:
        tree_a: First Data Tree (Grasshopper Tree A [tree]).
        tree_b: Second Data Tree (Grasshopper Tree B [tree]).
        offset: Relative offset for item combo (Grasshopper Offset [item]).
        wrap_paths: Wrap paths when the shift is out of bounds (Grasshopper Wrap Paths [item]).
        wrap_items: Wrap items when the shift is out of bounds (Grasshopper Wrap Items [item]).

    Outputs:
        item_a: Item in tree A (Grasshopper Item A).
        item_b: Relative item in tree B (Grasshopper Item B).

    Notes:
        Grasshopper: Sets > Tree > Relative Items (RelItem2).
        pyhopper decisions: Grasshopper-verified — the offset ``{0;+1}[+1]`` names a path offset and
        an optional item offset; every branch pairs its items with the items of the branch that many
        steps away (item ``i`` with item ``i + offset``), keeping only pairs that exist unless the
        wraps are on: wrapped paths cycle through the indices that exist among the paths sharing their
        prefix, wrapped items cycle within the branch. Both outputs sit at the source branch's path;
        branches without pairs vanish. An offset without a ``{…}`` block raises ``ValueError``.
        Item A comes from tree A, item B from the offset branch of tree B.
    """

    display_name = "Relative Items"
    nickname = "RelItem2"
    gh_guid = "2653b135-4df1-4a6b-820c-55e2ad3bc1e0"

    inputs = [
        InputParam("tree_a", None, Access.TREE),
        InputParam("tree_b", None, Access.TREE),
        InputParam("offset", str, Access.ITEM, default=""),
        InputParam("wrap_paths", bool, Access.ITEM, default=False),
        InputParam("wrap_items", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("item_a", access=Access.TREE),
        OutputParam("item_b", access=Access.TREE),
    ]

    def generate(self, tree_a=None, tree_b=None, offset="", wrap_paths=False, wrap_items=False):
        return relative_items(tree_a if tree_a is not None else DataTree(), tree_b if tree_b is not None else DataTree(), offset, bool(wrap_paths), bool(wrap_items))
