"""TrimTree - Reduce the complexity of a tree by merging the outermost branches (Grasshopper "Trim Tree")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class TrimTree(Component):
    """Reduce the complexity of a tree by merging the outermost branches.

    Inputs:
        tree: Data tree to flatten (Grasshopper Tree [tree]).
        depth: Number of outermost branches to merge (Grasshopper Depth [item]).

    Outputs:
        tree: Trimmed data tree (Grasshopper Tree).

    Notes:
        Grasshopper: Sets > Tree > Trim Tree (Trim).
        pyhopper decisions: removes the last ``depth`` indices of every path and merges the branches that
        collide; branches whose path is not longer than ``depth`` are omitted (Grasshopper
        drops them with a warning); a negative depth raises ``ValueError``; Grasshopper
        default ``depth = 1``.
    """

    display_name = "Trim Tree"
    nickname = "Trim"
    gh_guid = "1177d6ee-3993-4226-9558-52b7fd63e1e3"

    inputs = [
        InputParam("tree", None, Access.TREE),
        InputParam("depth", int, Access.ITEM, default=1),
    ]
    outputs = [
        OutputParam("tree", access=Access.TREE),
    ]

    def generate(self, tree=None, depth=1):
        return (DataTree() if tree is None else tree).trim(int(depth))
