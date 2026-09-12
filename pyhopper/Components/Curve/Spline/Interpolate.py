"""Interpolate - Create a NURBS curve through supplied vertices."""

from pyhopper.Core.Atoms import AtomicInterval, AtomicNurbsCurve, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import (
    interpolate_nurbs_curve,
    nurbs_curve_domain,
    nurbs_curve_length,
)



class Interpolate(Component):
    """Create an interpolated NURBS curve from each branch of vertices.

    Knot style values are ``0`` for uniform, ``1`` for chord spacing, and
    ``2`` for square-root chord spacing. Degree must be a positive odd number.
    """

    display_name = "Interpolate"
    nickname = "IntCrv"
    gh_guid = "2b2a4145-3dff-41d4-a8de-1ea9d29eef33"

    inputs = [
        InputParam("vertices", AtomicPoint, Access.LIST),
        InputParam("degree", int, Access.ITEM, default=3),
        InputParam("periodic", bool, Access.ITEM, default=False),
        InputParam("knot_style", int, Access.ITEM, default=1),
    ]
    outputs = [
        OutputParam("curve", AtomicNurbsCurve),
        OutputParam("length", float),
        OutputParam("domain", AtomicInterval),
    ]

    def generate(self, vertices=None, degree=3, periodic=False, knot_style=1):
        curve = interpolate_nurbs_curve(
            tuple(vertices or ()),
            int(degree),
            bool(periodic),
            int(knot_style),
        )
        domain_start, domain_end = nurbs_curve_domain(curve)
        return curve, nurbs_curve_length(curve), AtomicInterval(domain_start, domain_end)
