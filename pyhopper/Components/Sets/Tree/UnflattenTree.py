"""UnflattenTree - Unflatten a data tree by moving items back into branches (Grasshopper "Unflatten Tree")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class UnflattenTree(Component):
    """Unflatten a data tree by moving items back into branches.

    Inputs:
        tree: Data tree to unflatten (Grasshopper Tree [tree]).
        guide: Guide data tree that defines the path layout (Grasshopper Guide [tree]).

    Outputs:
        tree: Unflattened data tree (Grasshopper Tree).

    Notes:
        Grasshopper: Sets > Tree > Unflatten Tree (Unflatten).
        pyhopper decisions: the tree's items (all branches, in order) fill the guide's branches with
        the guide's item counts; a branch that cannot be filled completely is dropped and surplus
        items are ignored (Grasshopper-verified, it only warns); empty guide branches stay empty.
    """

    display_name = "Unflatten Tree"
    nickname = "Unflatten"
    gh_guid = "b8e2aa8f-8830-4ee1-bb59-613ea279c281"

    inputs = [
        InputParam("tree", None, Access.TREE),
        InputParam("guide", None, Access.TREE),
    ]
    outputs = [
        OutputParam("tree", access=Access.TREE),
    ]

    def generate(self, tree=None, guide=None):
        items = [] if tree is None else tree.all_items()
        target = DataTree() if guide is None else guide
        branches, cursor = {}, 0
        for path, branch in target.branches():
            size = len(branch)
            if cursor + size > len(items):
                break
            branches[path] = items[cursor: cursor + size]
            cursor += size
        return DataTree.from_branches(branches)
