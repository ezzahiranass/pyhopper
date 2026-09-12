"""EulerNumber - Returns a factor of the natural number (e) (Grasshopper "Natural logarithm")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class EulerNumber(Component):
    """Returns a factor of the natural number (e).

    Inputs:
        factor: Factor to be multiplied by e (Grasshopper Factor [item]).

    Outputs:
        result: Output value (Grasshopper Output).

    Notes:
        Grasshopper: Maths > Util > Natural logarithm (E).
        pyhopper decisions: ``factor * e`` like Grasshopper's Maths > Util "Natural logarithm" (E);
        the class is named after the constant to leave ``NaturalLogarithm`` to the Polynomials
        component that actually takes logarithms. Default factor 1.
    """

    display_name = "Natural logarithm"
    nickname = "E"
    gh_guid = "b6cac37c-21b9-46c6-bd0d-17ff67796578"

    inputs = [
        InputParam("factor", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("result", float),
    ]

    def generate(self, factor=1.0):
        return float(factor) * math.e
