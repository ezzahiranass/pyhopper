"""FlipCurve - Flip a curve using an optional guide curve (Grasshopper "Flip Curve")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveFitting import reverse_curve
from pyhopper.Utils.Curves import curve_domain_of, curve_tangent_at
from pyhopper.Utils.Vectors import dot
from pyhopper.Core.TypeSystem import CURVE


class FlipCurve(Component):
    """Flip a curve using an optional guide curve.

    Inputs:
        curve: Curve to flip (Grasshopper Curve [item]).
        guide: Optional guide curve (Grasshopper Guide [item]).

    Outputs:
        curve: Flipped curve (Grasshopper Curve).
        flag: Flip action (Grasshopper Flag).

    Notes:
        Grasshopper: Curve > Util > Flip Curve (Flip).
        pyhopper decisions: without a guide the curve is always reversed; with one it is reversed only
        when the start tangents point against each other (Grasshopper-verified: a perpendicular guide
        leaves the curve alone); ``flag`` says whether it was reversed. Lines, polylines, arcs, circles
        and rectangles keep their type, everything else becomes a NURBS curve.
    """

    display_name = "Flip Curve"
    nickname = "Flip"
    gh_guid = "22990b1f-9be6-477c-ad89-f775cd347105"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("guide", CURVE, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("curve", CURVE),
        OutputParam("flag", bool),
    ]

    def generate(self, curve=None, guide=None):
        if guide is not None:
            start, _ = curve_domain_of(curve)
            guide_start, _ = curve_domain_of(guide)
            if dot(curve_tangent_at(curve, start), curve_tangent_at(guide, guide_start)) >= 0.0:
                return curve, False
        return reverse_curve(curve), True
