"""Shatter - Shatter a curve into segments (Grasshopper "Shatter")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import shatter
from pyhopper.Core.TypeSystem import CURVE


class Shatter(Component):
    """Shatter a curve into segments.

    Inputs:
        curve: Curve to trim (Grasshopper Curve [item]).
        parameters: Parameters to split at (Grasshopper Parameters [list]).

    Outputs:
        segments: Shattered remains (Grasshopper Segments).

    Notes:
        Grasshopper: Curve > Division > Shatter (Shatter).
        pyhopper decisions: Grasshopper-verified — parameters are sorted, de-duplicated and clipped to
        the domain; pieces keep the input's type (lines, arcs of circles, polylines, NURBS sub-domains,
        sub-polycurves); on a closed curve the wrap-around piece comes last as a two-segment polycurve.
        No parameters give no pieces, parameters only at the ends give the whole curve. Polycurve segments keep their parameter spans the way Rhino assigns them (pieces of the input keep their parameter lengths, new segments get their natural span).
    """

    display_name = "Shatter"
    nickname = "Shatter"
    gh_guid = "2ad2a4d4-3de1-42f6-a4b8-f71835f35710"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameters", float, Access.LIST),
    ]
    outputs = [
        OutputParam("segments", CURVE, access=Access.LIST),
    ]

    def generate(self, curve=None, parameters=None):
        return shatter(curve, list(parameters or []))
