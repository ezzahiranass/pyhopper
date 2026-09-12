"""GoldenRatio - Returns a factor of the golden ratio (Phi) (Grasshopper "Golden Ratio")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math


class GoldenRatio(Component):
    """Returns a factor of the golden ratio (Phi).

    Inputs:
        factor: Factor to be multiplied by Phi (Grasshopper Factor [item]).

    Outputs:
        result: Output value (Grasshopper Output).

    Notes:
        Grasshopper: Maths > Util > Golden Ratio (Phi).
        pyhopper decisions: none; ``factor * (1 + sqrt(5)) / 2`` with factor 1 by default, as in Grasshopper.
    """

    display_name = "Golden Ratio"
    nickname = "Phi"
    gh_guid = "cb22d3ed-93d8-4629-bdf2-c0c7c25afd2c"

    inputs = [
        InputParam("factor", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, factor=1.0):
        return float(factor) * (1.0 + math.sqrt(5.0)) / 2.0
