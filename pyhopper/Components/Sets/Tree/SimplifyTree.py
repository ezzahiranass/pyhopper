"""SimplifyTree - Simplify a data tree by removing the overlap shared amongst all branches (Grasshopper "Simplify Tree")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class SimplifyTree(Component):
    """Simplify a data tree by removing the overlap shared amongst all branches.

    Inputs:
        tree: Data tree to simplify. (Grasshopper Tree [tree]).
        front: Limit path collapse to indices at the start of the path only. (Grasshopper Front [item]).

    Outputs:
        tree: Simplified data tree. (Grasshopper Tree).

    Notes:
        Grasshopper: Sets > Tree > Simplify Tree (Simplify).
        pyhopper decisions: removes every index position shared by all branches (``front`` limits it to the
        leading run); when that would empty the shortest path its first index is kept, and
        a single-branch tree is returned unchanged — all exactly as Grasshopper does.
    """

    display_name = "Simplify Tree"
    nickname = "Simplify"
    gh_guid = "1303da7b-e339-4e65-a051-82c4dce8224d"

    inputs = [
        InputParam("tree", None, Access.TREE),
        InputParam("front", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("tree", access=Access.TREE),
    ]

    def generate(self, tree=None, front=False):
        return (DataTree() if tree is None else tree).simplify(bool(front))
