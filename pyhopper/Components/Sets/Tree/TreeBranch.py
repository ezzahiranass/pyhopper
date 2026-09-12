"""TreeBranch - Retrieve a specific branch from a data tree (Grasshopper "Tree Branch")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path


class TreeBranch(Component):
    """Retrieve a specific branch from a data tree.

    Inputs:
        tree: Data Tree (Grasshopper Tree [tree]).
        path: Data tree branch path (Grasshopper Path [item]).

    Outputs:
        data: Branch at {P} (Grasshopper Branch).

    Notes:
        Grasshopper: Sets > Tree > Tree Branch (Branch).
        pyhopper decisions: Grasshopper-verified — the branch is emitted at the requested path itself
        (a missing path gives an empty branch there, where Grasshopper also warns); several requests
        for one path concatenate.
    """

    display_name = "Tree Branch"
    nickname = "Branch"
    gh_guid = "3a710c1e-1809-4e19-8c15-82adce31cd62"

    inputs = [
        InputParam("tree", None, Access.TREE),
        InputParam("path", Path, Access.ITEM, default=Path(0)),
    ]
    outputs = [
        OutputParam("data", access=Access.TREE),
    ]

    def generate(self, tree=None, path=Path(0)):
        source = tree if tree is not None else DataTree()
        return DataTree.from_branches({path: list(source.branch(path)) if path in source.paths else []})
