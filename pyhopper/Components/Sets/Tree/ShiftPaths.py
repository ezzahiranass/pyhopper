"""ShiftPaths - Shift the indices in all data tree paths (Grasshopper "Shift Paths")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path


class ShiftPaths(Component):
    """Shift the indices in all data tree paths.

    Inputs:
        data: Data to modify (Grasshopper Data [tree]).
        offset: Offset to apply to each branch (Grasshopper Offset [item]).

    Outputs:
        data: Shifted data (Grasshopper Data).

    Notes:
        Grasshopper: Sets > Tree > Shift Paths (PShift).
        pyhopper decisions: Grasshopper-verified — a negative offset drops that many indices from
        the end of every path (``{0;1}`` → ``{0}``), a positive one from the start; branches that
        land on the same path merge in order, and a path shifted out of existence is dropped
        (Grasshopper warns). Default offset -1.
    """

    display_name = "Shift Paths"
    nickname = "PShift"
    gh_guid = "2d61f4e0-47c5-41d6-a41d-6afa96ee63af"

    inputs = [
        InputParam("data", None, Access.TREE),
        InputParam("offset", int, Access.ITEM, default=-1),
    ]
    outputs = [
        OutputParam("data", access=Access.TREE),
    ]

    def generate(self, data=None, offset=-1):
        source = DataTree() if data is None else data
        shift = int(offset)
        branches: dict[Path, list] = {}
        for path, branch in source.branches():
            indices = tuple(path)
            kept = indices[shift:] if shift >= 0 else indices[:len(indices) + shift]
            if not kept:
                continue  # shifted out of existence
            branches.setdefault(Path(*kept), []).extend(branch)
        return DataTree.from_branches(branches)
