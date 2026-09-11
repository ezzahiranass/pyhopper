"""GraftTree - Graft a data tree by adding an extra branch for every item (Grasshopper "Graft Tree")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class GraftTree(Component):
    """Graft a data tree by adding an extra branch for every item.

    Inputs:
        tree: Data tree to graft (Grasshopper Tree [tree]).

    Outputs:
        tree: Grafted data tree (Grasshopper Tree).

    Notes:
        Grasshopper: Sets > Tree > Graft Tree (Graft).
        pyhopper decisions: empty branches survive as empty sub-branches (``{5}`` -> ``{5;0}``), like Grasshopper.
    """

    display_name = "Graft Tree"
    nickname = "Graft"
    gh_guid = "87e1d9ef-088b-4d30-9dda-8a7448a17329"

    inputs = [
        InputParam("tree", None, Access.TREE),
    ]
    outputs = [
        OutputParam("tree", access=Access.TREE),
    ]

    def generate(self, tree=None):
        return (DataTree() if tree is None else tree).graft()
