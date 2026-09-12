"""SmoothNumbers - Smooth out changing numbers over time (Grasshopper "Smooth Numbers")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class SmoothNumbers(Component):
    """Smooth out changing numbers over time.

    Inputs:
        numbers: Changing numbers (Grasshopper Numbers [tree]).

    Outputs:
        numbers: Smoothened numbers (Grasshopper Numbers).

    Notes:
        Grasshopper: Maths > Util > Smooth Numbers (Smooth).
        pyhopper decisions: Grasshopper smooths values across successive solutions of the same
        definition; pyhopper solves once and has no history, so the tree passes through unchanged
        (Grasshopper-verified for a single solution).
    """

    display_name = "Smooth Numbers"
    nickname = "Smooth"
    gh_guid = "5b424e1c-d061-43cd-8c20-db84564b0502"

    inputs = [
        InputParam("numbers", float, Access.TREE, optional=True),
    ]
    outputs = [
        OutputParam("numbers", float, access=Access.TREE),
    ]

    def generate(self, numbers=None):
        return DataTree() if numbers is None else numbers
