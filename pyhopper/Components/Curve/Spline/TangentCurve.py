"""TangentCurve - Create a curve through a set of points with tangents (Grasshopper "Tangent Curve")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import tangent_curve
from pyhopper.Core.TypeSystem import CURVE


class TangentCurve(Component):
    """Create a curve through a set of points with tangents.

    Inputs:
        vertices: Interpolation points (Grasshopper Vertices [list]).
        tangents: Tangent vectors for all interpolation points (Grasshopper Tangents [list]).
        blend: Blend factor (Grasshopper Blend [item]).
        degree: Curve degree (only odd degrees are supported) (Grasshopper Degree [item]).

    Outputs:
        curve: Resulting nurbs curve (Grasshopper Curve).
        length: Curve length (Grasshopper Length).
        domain: Curve domain (Grasshopper Domain).

    Notes:
        Grasshopper: Curve > Spline > Tangent Curve (TanCurve).
        pyhopper decisions: Grasshopper-verified — a clamped uniform B-spline whose control polygon
        leaves every vertex along its (unitised) tangent by ``blend × chord`` with ``(degree − 1) / 2``
        handle points per side; degrees below 3 become 3 and even degrees are raised by one (as
        Grasshopper does with a warning); the knot domain is the curve length, which is also the Length
        and Domain outputs. Unequal vertex/tangent counts raise ``ValueError``. Defaults 0.5, 3.
    """

    display_name = "Tangent Curve"
    nickname = "TanCurve"
    gh_guid = "f73498c5-178b-4e09-ad61-73d172fa6e56"

    inputs = [
        InputParam("vertices", AtomicPoint, Access.LIST),
        InputParam("tangents", AtomicVector, Access.LIST),
        InputParam("blend", float, Access.ITEM, default=0.5),
        InputParam("degree", int, Access.ITEM, default=3),
    ]
    outputs = [
        OutputParam("curve", CURVE),
        OutputParam("length", float),
        OutputParam("domain", AtomicInterval),
    ]

    def generate(self, vertices=None, tangents=None, blend=0.5, degree=3):
        return tangent_curve(list(vertices or []), list(tangents or []), float(blend), int(degree))
