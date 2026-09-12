"""DeconstructPath - Deconstruct a data tree path into individual integers (Grasshopper "Deconstruct Path")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Path import Path


class DeconstructPath(Component):
    """Deconstruct a data tree path into individual integers.

    Inputs:
        branch: Branch path (Grasshopper Branch [item]).

    Outputs:
        indices: Branch path indices (Grasshopper Indices).

    Notes:
        Grasshopper: Sets > Tree > Deconstruct Path (DPath).
        pyhopper decisions: none; the path's indices as a list.
    """

    display_name = "Deconstruct Path"
    nickname = "DPath"
    gh_guid = "df6d9197-9a6e-41a2-9c9d-d2221accb49e"

    inputs = [
        InputParam("branch", Path, Access.ITEM, default=Path(0)),
    ]
    outputs = [
        OutputParam("indices", int, access=Access.LIST),
    ]

    def generate(self, branch=Path(0)):
        return list(branch)
