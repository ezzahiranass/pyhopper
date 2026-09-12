"""LengthParameter - Measure the length of a curve to and from a parameter (Grasshopper "Length Parameter")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_length, curve_length_at
from pyhopper.Core.TypeSystem import CURVE


class LengthParameter(Component):
    """Measure the length of a curve to and from a parameter.

    Inputs:
        curve: Curve to measure (Grasshopper Curve [item]).
        parameter: Parameter along curve (Grasshopper Parameter [item]).

    Outputs:
        length_before: Curve length from start to parameter (Grasshopper Length).
        length_after: Curve length from parameter to end (Grasshopper Length).

    Notes:
        Grasshopper: Curve > Analysis > Length Parameter (LenP).
        pyhopper decisions: lengths before and after the parameter along the curve, in the curve's own
        parameterisation (see Evaluate Curve).
    """

    display_name = "Length Parameter"
    nickname = "LenP"
    gh_guid = "a1c16251-74f0-400f-9e7c-5e379d739963"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameter", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("length_before", float),
        OutputParam("length_after", float),
    ]

    def generate(self, curve=None, parameter=0.0):
        before = curve_length_at(curve, parameter)
        return before, curve_length(curve) - before
