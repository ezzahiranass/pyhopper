"""FlipMatrix - Flip a matrix-like data tree by swapping rows and columns (Grasshopper "Flip Matrix")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class FlipMatrix(Component):
    """Flip a matrix-like data tree by swapping rows and columns.

    Inputs:
        data: Data matrix to flip (Grasshopper Data [tree]).

    Outputs:
        data: Flipped data matrix (Grasshopper Data).

    Notes:
        Grasshopper: Sets > Tree > Flip Matrix (Flip).
        pyhopper decisions: paths must have the same length and may differ at one index position only
        (``ValueError`` otherwise, where Grasshopper reports an error); shorter branches are
        padded with ``None`` (Grasshopper nulls).
    """

    display_name = "Flip Matrix"
    nickname = "Flip"
    gh_guid = "41aa4112-9c9b-42f4-847e-503b9d90e4c7"

    inputs = [
        InputParam("data", None, Access.TREE),
    ]
    outputs = [
        OutputParam("data", access=Access.TREE),
    ]

    def generate(self, data=None):
        return (DataTree() if data is None else data).flip_matrix()
