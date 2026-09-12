"""CleanTree - Removed all null and invalid items from a data tree (Grasshopper "Clean Tree")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class CleanTree(Component):
    """Removed all null and invalid items from a data tree.

    Inputs:
        remove_nulls: Remove null items from the tree. (Grasshopper Remove Nulls [item]).
        remove_invalid: Remove invalid items from the tree. (Grasshopper Remove Invalid [item]).
        remove_empty: Remove empty branches from the tree. (Grasshopper Remove Empty [item]).
        tree: Data tree to clean (Grasshopper Tree [tree]).

    Outputs:
        tree: Spotless data tree (Grasshopper Tree).

    Notes:
        Grasshopper: Sets > Tree > Clean Tree (Clean).
        pyhopper decisions: ``None`` items are Grasshopper nulls; pyhopper atoms are always valid, so
        "invalid" removes non-finite numbers; Grasshopper defaults ``True`` / ``True`` /
        ``False`` (empty branches are kept unless asked).
    """

    display_name = "Clean Tree"
    nickname = "Clean"
    gh_guid = "071c3940-a12d-4b77-bb23-42b5d3314a0d"

    inputs = [
        InputParam("remove_nulls", bool, Access.ITEM, default=True),
        InputParam("remove_invalid", bool, Access.ITEM, default=True),
        InputParam("remove_empty", bool, Access.ITEM, default=False),
        InputParam("tree", None, Access.TREE),
    ]
    outputs = [
        OutputParam("tree", access=Access.TREE),
    ]

    def generate(self, remove_nulls=True, remove_invalid=True, remove_empty=False, tree=None):
        return (DataTree() if tree is None else tree).clean(bool(remove_nulls), bool(remove_invalid), bool(remove_empty))
