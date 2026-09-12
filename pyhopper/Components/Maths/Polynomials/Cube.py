"""Cube - Compute the cube of a value (Grasshopper "Cube")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Cube(Component):
    """Compute the cube of a value.

    Inputs:
        value: Input value (Grasshopper Value [item]).

    Outputs:
        result: Output value (Grasshopper Result).

    Notes:
        Grasshopper: Maths > Polynomials > Cube (Cube).
        pyhopper decisions: none; behaviour matches Grasshopper.
    """

    display_name = "Cube"
    nickname = "Cube"
    gh_guid = "7e3185eb-a38c-4949-bcf2-0e80dee3a344"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, value=0.0):
        x = float(value)
        return x * x * x
