"""TreeStatistics - Get some statistics regarding a data tree (Grasshopper "Tree Statistics")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path


class TreeStatistics(Component):
    """Get some statistics regarding a data tree.

    Inputs:
        tree: Data Tree to analyze (Grasshopper Tree [tree]).

    Outputs:
        branch_paths: All the paths of the tree (Grasshopper Paths).
        length: The length of each branch in the tree (Grasshopper Length).
        count: Number of paths and branches in the tree (Grasshopper Count).

    Notes:
        Grasshopper: Sets > Tree > Tree Statistics (TStat).
        pyhopper decisions: Grasshopper-verified — the paths, their item counts and the branch count,
        all placed at the tree's first path like Grasshopper.
    """

    display_name = "Tree Statistics"
    nickname = "TStat"
    gh_guid = "99bee19d-588c-41a0-b9b9-1d00fb03ea1a"

    inputs = [
        InputParam("tree", None, Access.TREE),
    ]
    outputs = [
        OutputParam("branch_paths", Path, access=Access.LIST),
        OutputParam("length", int, access=Access.LIST),
        OutputParam("count", int),
    ]

    def generate(self, tree=None):
        source = tree if tree is not None else DataTree()
        paths = list(source.paths)
        return paths, [len(list(source.branch(path))) for path in paths], len(paths)
