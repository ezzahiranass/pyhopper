"""Epsilon - Returns a factor of double precision floating point epsilon (Grasshopper "Epsilon")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

# .NET Double.Epsilon: the smallest positive subnormal double
DOUBLE_EPSILON = 5e-324


class Epsilon(Component):
    """Returns a factor of double precision floating point epsilon.

    Inputs:
        factor: Factor to be multiplied by epsilon (Grasshopper Factor [item]).

    Outputs:
        result: Output value (Grasshopper Output).

    Notes:
        Grasshopper: Maths > Util > Epsilon (Eps).
        pyhopper decisions: Grasshopper's epsilon is .NET ``Double.Epsilon``, the smallest positive
        double (4.94e-324), not the machine epsilon; the factor scales it (default 1).
    """

    display_name = "Epsilon"
    nickname = "Eps"
    gh_guid = "deadf87d-99a6-4980-90c3-f98350aa6f0f"

    inputs = [
        InputParam("factor", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, factor=1.0):
        return float(factor) * DOUBLE_EPSILON
