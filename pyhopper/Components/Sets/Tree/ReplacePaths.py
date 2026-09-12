"""ReplacePaths - Find & replace paths in a data tree (Grasshopper "Replace Paths")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Utils.PathMasks import parse_path_mask
from pyhopper.Core.Path import Path


class ReplacePaths(Component):
    """Find & replace paths in a data tree.

    Inputs:
        data: Data stream to process (Grasshopper Data [tree]).
        search: Search masks (Grasshopper Search [list]).
        replace: Respective replacement paths (Grasshopper Replace [list]).

    Outputs:
        data: Processed tree data (Grasshopper Data).

    Notes:
        Grasshopper: Sets > Tree > Replace Paths (Replace).
        pyhopper decisions: Grasshopper-verified — every branch moves to the replacement paired with
        the first search mask it matches (branches landing on one path concatenate, unmatched branches
        stay); unequal mask and path counts raise ``ValueError`` (Grasshopper reports an error).
    """

    display_name = "Replace Paths"
    nickname = "Replace"
    gh_guid = "bfaaf799-77dc-4f31-9ad8-2f7d1a80aeb0"

    inputs = [
        InputParam("data", None, Access.TREE),
        InputParam("search", str, Access.LIST),
        InputParam("replace", Path, Access.LIST),
    ]
    outputs = [
        OutputParam("data", access=Access.TREE),
    ]

    def generate(self, data=None, search=None, replace=None):
        masks = [parse_path_mask(mask) for mask in (search or [])]
        targets = list(replace or [])
        if len(masks) != len(targets):
            raise ValueError("ReplacePaths needs as many replacement paths as search masks")
        source = data if data is not None else DataTree()
        branches: dict = {}
        for path in source.paths:
            destination = next((target for mask, target in zip(masks, targets) if mask.matches(path)), path)
            branches.setdefault(destination, []).extend(source.branch(path))
        return DataTree.from_branches(branches)
