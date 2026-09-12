"""ConstructPath - Construct a data tree branch path (Grasshopper "Construct Path")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Path import Path


class ConstructPath(Component):
    """Construct a data tree branch path.

    Inputs:
        indices: Branch path indices (Grasshopper Indices [list]).

    Outputs:
        path: Branch path (Grasshopper Branch).

    Notes:
        Grasshopper: Sets > Tree > Construct Path (Path).
        pyhopper decisions: none — the indices become a path (negative indices are kept, as in
        Grasshopper); an empty list emits nothing (Grasshopper emits null).
    """

    display_name = "Construct Path"
    nickname = "Path"
    gh_guid = "946cb61e-18d2-45e3-8840-67b0efa26528"

    inputs = [
        InputParam("indices", int, Access.LIST),
    ]
    outputs = [
        OutputParam("path", Path),
    ]

    def generate(self, indices=None):
        values = [int(index) for index in (indices or [])]
        return Path(*values) if values else Component.NO_OUTPUT
