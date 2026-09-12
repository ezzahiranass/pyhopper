"""FlattenTree - Flatten a data tree by removing all branching information (Grasshopper "Flatten Tree")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path


class FlattenTree(Component):
    """Flatten a data tree by removing all branching information.

    Inputs:
        tree: Data tree to flatten (Grasshopper Tree [tree]).
        path: Path of flattened tree (Grasshopper Path [item]).

    Outputs:
        tree: Flattened data tree (Grasshopper Tree).

    Notes:
        Grasshopper: Sets > Tree > Flatten Tree (Flatten).
        pyhopper decisions: every branch collapses into the given path (Grasshopper default ``{0}``); a
        path input with several items flattens into each of them (Grasshopper keeps
        only the last). Text such as ``"{2;3}"`` is accepted on the path port.
    """

    display_name = "Flatten Tree"
    nickname = "Flatten"
    gh_guid = "f80cfe18-9510-4b89-8301-8e58faf423bb"

    inputs = [
        InputParam("tree", None, Access.TREE),
        InputParam("path", Path, Access.ITEM, default=Path(0)),
    ]
    outputs = [
        OutputParam("tree", access=Access.TREE),
    ]

    def generate(self, tree=None, path=Path(0)):
        return (DataTree() if tree is None else tree).flatten(path)
