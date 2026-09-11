"""SumSurface - Create a sum surface from two edge curves (Grasshopper "Sum Surface")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import SURFACE
from pyhopper.Utils.SurfaceBuilders import sum_surface
from pyhopper.Core.TypeSystem import CURVE


class SumSurface(Component):
    """Create a sum surface from two edge curves.

    Inputs:
        curve_a: First curve (Grasshopper Curve A [item]).
        curve_b: Second curve (Grasshopper Curve B [item]).

    Outputs:
        surface: BRep representing the sum-surface (Grasshopper Surface).

    Notes:
        Grasshopper: Surface > Freeform > Sum Surface (SumSrf).
        pyhopper decisions: the translational surface ``A(u) + B(v) - B(start)`` with A's knots in U and B's in V and
        multiplied weights, exactly Grasshopper's; polylines give one kinked surface where
        Grasshopper splits faces.
    """

    display_name = "Sum Surface"
    nickname = "SumSrf"
    gh_guid = "5e33c760-adcd-4235-b1dd-05cf72eb7a38"

    inputs = [
        InputParam("curve_a", CURVE, Access.ITEM),
        InputParam("curve_b", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
    ]

    def generate(self, curve_a=None, curve_b=None):
        from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
        return sum_surface(as_nurbs_curve(curve_a), as_nurbs_curve(curve_b))
