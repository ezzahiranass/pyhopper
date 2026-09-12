"""CubeRoot - Compute the cube root of a value (Grasshopper "Cube Root")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math


class CubeRoot(Component):
    """Compute the cube root of a value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > Cube Root (Cbrt).
        pyhopper decisions: the real cube root, so negative values give negative roots as in Grasshopper.
    """

    display_name = "Cube Root"
    nickname = "Cbrt"
    gh_guid = "5b0be57a-31f5-4446-a11a-ae0d348bca90"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        return math.cbrt(float(value))
