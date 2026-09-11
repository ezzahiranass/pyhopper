"""Pi - Returns a factor of Pi (Grasshopper "Pi")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Pi(Component):
    """Returns a factor of Pi.

    Inputs:
        factor: Factor to be multiplied by Pi (Grasshopper Factor [item]).

    Outputs:
        result: Output value (Grasshopper Output).

    Notes:
        Grasshopper: Maths > Util > Pi (Pi).
        pyhopper decisions: none; behaviour matches Grasshopper.
    """

    display_name = "Pi"
    nickname = "Pi"
    gh_guid = "0d2ccfb3-9d41-4759-9452-da6a522c3eaa"

    inputs = [
        InputParam("factor", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, factor=1.0):
        return float(factor) * math.pi
