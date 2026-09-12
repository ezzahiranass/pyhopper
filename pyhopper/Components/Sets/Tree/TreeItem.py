"""TreeItem - Retrieve a specific item from a data tree (Grasshopper "Tree Item")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path


class TreeItem(Component):
    """Retrieve a specific item from a data tree.

    Inputs:
        tree: Data Tree (Grasshopper Tree [tree]).
        path: Data tree branch path (Grasshopper Path [item]).
        index: Item index (Grasshopper Index [item]).
        wrap: Wrap index to list bounds (Grasshopper Wrap [item]).

    Outputs:
        element: Item at {P:i'} (Grasshopper Element).

    Notes:
        Grasshopper: Sets > Tree > Tree Item (Item).
        pyhopper decisions: Grasshopper-verified — the item at ``index`` of the branch at ``path``
        (negative and out-of-range indices wrap when ``wrap`` is on, default True); a missing path or
        an index out of range emits nothing (Grasshopper emits null with a warning). Like
        Grasshopper, single-branch path/index inputs land the items at the tree's first path.
    """

    display_name = "Tree Item"
    nickname = "Item"
    gh_guid = "c1ec65a3-bda4-4fad-87d0-edf86ed9d81c"

    inputs = [
        InputParam("tree", None, Access.TREE),
        InputParam("path", Path, Access.ITEM, default=Path(0)),
        InputParam("index", int, Access.ITEM, default=0),
        InputParam("wrap", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("element"),
    ]

    def generate(self, tree=None, path=Path(0), index=0, wrap=True):
        source = tree if tree is not None else DataTree()
        if path not in source.paths:
            return Component.NO_OUTPUT
        items = list(source.branch(path))
        position = int(index)
        if wrap and items:
            position %= len(items)
        if not 0 <= position < len(items):
            return Component.NO_OUTPUT
        return items[position]
