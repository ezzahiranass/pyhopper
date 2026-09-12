"""MatchTree - Match one data tree with another (Grasshopper "Match Tree")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class MatchTree(Component):
    """Match one data tree with another.

    Inputs:
        tree: Data tree to modify (Grasshopper Tree [tree]).
        guide: Data tree to match (Grasshopper Guide [tree]).

    Outputs:
        tree: Matched data tree containing the data of T but the layout of G (Grasshopper Tree).

    Notes:
        Grasshopper: Sets > Tree > Match Tree (Match).
        pyhopper decisions: the tree's branches take the guide's paths in order (item counts may
        differ); the two trees must have the same number of branches, otherwise ``ValueError``
        (Grasshopper: "Input trees must have equal number of paths").
    """

    display_name = "Match Tree"
    nickname = "Match"
    gh_guid = "46372d0d-82dc-4acb-adc3-25d1fde04c4e"

    inputs = [
        InputParam("tree", None, Access.TREE),
        InputParam("guide", None, Access.TREE),
    ]
    outputs = [
        OutputParam("tree", access=Access.TREE),
    ]

    def generate(self, tree=None, guide=None):
        source = DataTree() if tree is None else tree
        target = DataTree() if guide is None else guide
        if source.branch_count != target.branch_count:
            raise ValueError("MatchTree needs trees with the same number of branches")
        return DataTree.from_branches({
            guide_path: list(branch) for guide_path, (_, branch) in zip(target.paths, source.branches())
        })
