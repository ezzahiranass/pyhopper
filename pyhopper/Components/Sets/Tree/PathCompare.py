"""PathCompare - Compare a path to a mask pattern (Grasshopper "Path Compare")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.PathMasks import path_matches
from pyhopper.Core.Path import Path


class PathCompare(Component):
    """Compare a path to a mask pattern.

    Inputs:
        path: Path to compare (Grasshopper Path [item]).
        mask: Comparison mask (Grasshopper Mask [item]).

    Outputs:
        comparison: Comparison (True = Match, False = Mismatch) (Grasshopper Comparison).

    Notes:
        Grasshopper: Sets > Tree > Path Compare (Compare).
        pyhopper decisions: Grasshopper's rule notation (``Utils/PathMasks.py``): ``{0;?}``, ``{0;*}``,
        ``{0;(1,2)}``, ``{0;(1 to 3)}``, ``{0;!1}``, ``{>1}``, ``{<=2}`` — Grasshopper-verified; invalid
        notation (text outside the braces, negative integers, empty rules) raises ``ValueError``
        where Grasshopper emits null. Default mask ``{*}`` (Grasshopper's default ``*`` is rejected by
        its own parser).
    """

    display_name = "Path Compare"
    nickname = "Compare"
    gh_guid = "1d8b0e2c-e772-4fa9-b7f7-b158251b34b8"

    inputs = [
        InputParam("path", Path, Access.ITEM, default=Path(0)),
        InputParam("mask", str, Access.ITEM, default="{*}"),
    ]
    outputs = [
        OutputParam("comparison", bool),
    ]

    def generate(self, path=Path(0), mask="{*}"):
        return path_matches(path, mask)
