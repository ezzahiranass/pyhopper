"""ControlPointLoft - Create a loft through curve control points (Grasshopper "Control Point Loft")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.SurfaceBuilders import control_point_loft
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Core.TypeSystem import CURVE, SURFACE


class ControlPointLoft(Component):
    """Create a loft through curve control points.

    Inputs:
        curves: Section curves (Grasshopper Curves [list]).
        degree: Degree perpendicular to curve direction (Grasshopper Degree [item]).

    Outputs:
        surface: Loft result (Grasshopper Surface).

    Notes:
        Grasshopper: Surface > Freeform > Control Point Loft (CPLoft).
        pyhopper decisions: the curves' control points become the pole rows; V is a clamped uniform
        B-spline of degree ``min(degree, curves - 1)`` (Grasshopper warns and clamps the same way);
        curves must share control-point count and degree, otherwise ``ValueError``. Default degree 5.
    """

    display_name = "Control Point Loft"
    nickname = "CPLoft"
    gh_guid = "5c270622-ee80-45a4-b07a-bd8ffede92a2"

    inputs = [
        InputParam("curves", CURVE, Access.LIST),
        InputParam("degree", int, Access.ITEM, default=5),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
    ]

    def generate(self, curves=None, degree=5):
        return control_point_loft([as_nurbs_curve(curve) for curve in (curves or [])], int(degree))
