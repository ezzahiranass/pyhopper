"""BlendCurve - Create a blend curve between two curves (Grasshopper "Blend Curve")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import blend_curve
from pyhopper.Core.TypeSystem import CURVE


class BlendCurve(Component):
    """Create a blend curve between two curves.

    Inputs:
        curve_a: First curve for blend (Grasshopper Curve A [item]).
        curve_b: Second curve for blend (Grasshopper Curve B [item]).
        bulge_a: Bulge factor at A (Grasshopper Bulge A [item]).
        bulge_b: Bulge factor at B (Grasshopper Bulge B [item]).
        continuity: Continuity of blend (0=position, 1=tangency, 2=curvature) (Grasshopper Continuity [item]).

    Outputs:
        blend: Blend curve connecting the end of A to the start of B (Grasshopper Blend).

    Notes:
        Grasshopper: Curve > Spline > Blend Curve (BlendC).
        pyhopper decisions: Grasshopper-verified — from the end of A to the start of B: continuity 0 is
        a line, 1 a cubic Bézier with handles ``bulge × chord``, 2 (and any other value, as
        Grasshopper assumes curvature) a quintic with handles ``0.4 × bulge × chord`` and curvature
        terms ``1.25 × κ × handle²``; the NURBS domain is the blend's arc length. Defaults 1, 1, 2.
    """

    display_name = "Blend Curve"
    nickname = "BlendC"
    gh_guid = "5909dbcb-4950-4ce4-9433-7cf9e62ee011"

    inputs = [
        InputParam("curve_a", CURVE, Access.ITEM),
        InputParam("curve_b", CURVE, Access.ITEM),
        InputParam("bulge_a", float, Access.ITEM, default=1.0),
        InputParam("bulge_b", float, Access.ITEM, default=1.0),
        InputParam("continuity", int, Access.ITEM, default=2),
    ]
    outputs = [
        OutputParam("blend", CURVE),
    ]

    def generate(self, curve_a=None, curve_b=None, bulge_a=1.0, bulge_b=1.0, continuity=2):
        return blend_curve(curve_a, curve_b, float(bulge_a), float(bulge_b), int(continuity))
