"""BlendCurvePt - Create a blend curve between two curves that intersects a point (Grasshopper "Blend Curve Pt")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import blend_curve_through_point
from pyhopper.Core.TypeSystem import CURVE


class BlendCurvePt(Component):
    """Create a blend curve between two curves that intersects a point.

    Inputs:
        curve_a: First curve for blend (Grasshopper Curve A [item]).
        curve_b: Second curve for blend (Grasshopper Curve B [item]).
        point: Point for blend intersection (Grasshopper Point [item]).
        continuity: Continuity of blend (1=tangency, 2=curvature) (Grasshopper Continuity [item]).

    Outputs:
        blend: Blend curve connecting the end of A to the start of B, ideally coincident with P (Grasshopper Blend).

    Notes:
        Grasshopper: Curve > Spline > Blend Curve Pt (BlendCPt).
        pyhopper decisions: Grasshopper-verified — the blend (see Blend Curve) with equal bulges solved
        so the curve passes through the point; continuity 0 is treated as tangency like Grasshopper.
        pyhopper solves the bulge exactly (Grasshopper stops within about 1e-4 of the point) and
        raises ``ValueError`` when no bulge reaches the point, where Grasshopper emits a runaway curve
        with an error. Default continuity 2.
    """

    display_name = "Blend Curve Pt"
    nickname = "BlendCPt"
    gh_guid = "14cf43b6-5eb9-460f-899c-bdece732213a"

    inputs = [
        InputParam("curve_a", CURVE, Access.ITEM),
        InputParam("curve_b", CURVE, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("continuity", int, Access.ITEM, default=2),
    ]
    outputs = [
        OutputParam("blend", CURVE),
    ]

    def generate(self, curve_a=None, curve_b=None, point=AtomicPoint.origin(), continuity=2):
        return blend_curve_through_point(curve_a, curve_b, point, int(continuity))
