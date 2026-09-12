"""SplitTree - Split a data tree into two parts using path masks (Grasshopper "Split Tree")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Utils.PathMasks import parse_path_mask


class SplitTree(Component):
    """Split a data tree into two parts using path masks.

    Inputs:
        data: Tree to split (Grasshopper Data [tree]).
        masks: Splitting masks (Grasshopper Masks [list]).

    Outputs:
        positive: Positive set of data (all branches that match any of the masks) (Grasshopper Positive).
        negative: Negative set of data (all branches that do not match any of the masks (Grasshopper Negative).

    Notes:
        Grasshopper: Sets > Tree > Split Tree (Split).
        pyhopper decisions: none — branches matching any mask (rule notation, see Path Compare) go to
        the positive tree, the rest to the negative tree; invalid notation raises ``ValueError``.
    """

    display_name = "Split Tree"
    nickname = "Split"
    gh_guid = "d8b1e7ac-cd31-4748-b262-e07e53068afc"

    inputs = [
        InputParam("data", None, Access.TREE),
        InputParam("masks", str, Access.LIST),
    ]
    outputs = [
        OutputParam("positive", access=Access.TREE),
        OutputParam("negative", access=Access.TREE),
    ]

    def generate(self, data=None, masks=None):
        rules = [parse_path_mask(mask) for mask in (masks or [])]
        source = data if data is not None else DataTree()
        positive, negative = {}, {}
        for path in source.paths:
            (positive if any(rule.matches(path) for rule in rules) else negative)[path] = list(source.branch(path))
        return DataTree.from_branches(positive), DataTree.from_branches(negative)
