"""PruneTree - Remove small branches from a Data Tree (Grasshopper "Prune Tree")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class PruneTree(Component):
    """Remove small branches from a Data Tree.

    Inputs:
        tree: Data tree to prune (Grasshopper Tree [tree]).
        minimum: Remove branches with fewer than N0 items. (Grasshopper Minimum [item]).
        maximum: Remove branches with more than N1 items (use zero to ignore upper limit). (Grasshopper Maximum [item]).

    Outputs:
        tree: Pruned tree (Grasshopper Tree).

    Notes:
        Grasshopper: Sets > Tree > Prune Tree (Prune).
        pyhopper decisions: drops branches with fewer than ``minimum`` or more than ``maximum`` items;
        ``maximum = 0`` means no upper limit (Grasshopper defaults ``0`` / ``0``).
    """

    display_name = "Prune Tree"
    nickname = "Prune"
    gh_guid = "fe769f85-8900-45dd-ba11-ec9cd6c778c6"

    inputs = [
        InputParam("tree", None, Access.TREE),
        InputParam("minimum", int, Access.ITEM, default=0),
        InputParam("maximum", int, Access.ITEM, default=0),
    ]
    outputs = [
        OutputParam("tree", access=Access.TREE),
    ]

    def generate(self, tree=None, minimum=0, maximum=0):
        return (DataTree() if tree is None else tree).prune(int(minimum), int(maximum))
