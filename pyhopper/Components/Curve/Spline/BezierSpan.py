"""BezierSpan - Construct a bezier span from endpoints and tangents (Grasshopper "Bezier Span")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicInterval, AtomicNurbsCurve
from pyhopper.Utils.Curves import curve_length
from pyhopper.Utils.Vectors import translate
from pyhopper.Core.TypeSystem import CURVE


class BezierSpan(Component):
    """Construct a bezier span from endpoints and tangents.

    Inputs:
        start_point: Start of curve (Grasshopper Start point [item]).
        start_tangent: Tangent at start (Grasshopper Start tangent [item]).
        end_point: End of curve (Grasshopper End point [item]).
        end_tangent: Tangent at end (Grasshopper End tangent [item]).

    Outputs:
        curve: Resulting bezier span (Grasshopper Curve).
        length: Curve length (Grasshopper Length).
        domain: Curve domain (Grasshopper Domain).

    Notes:
        Grasshopper: Curve > Spline > Bezier Span (BzSpan).
        pyhopper decisions: a cubic Bézier with control points ``A, A + At, B + Bt, B`` — both tangent
        vectors are added to their end point at full length, not scaled by a third (Grasshopper-
        verified); the domain is [0, 1] and the length is measured numerically.
    """

    display_name = "Bezier Span"
    nickname = "BzSpan"
    gh_guid = "30ce59ce-22a1-49ee-9e21-e6d16b3684a8"

    inputs = [
        InputParam("start_point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("start_tangent", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
        InputParam("end_point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("end_tangent", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
    ]
    outputs = [
        OutputParam("curve", CURVE),
        OutputParam("length", float),
        OutputParam("domain", AtomicInterval),
    ]

    def generate(self, start_point=AtomicPoint.origin(), start_tangent=AtomicVector.unit_z(), end_point=AtomicPoint.origin(), end_tangent=AtomicVector.unit_z()):
        controls = (start_point, translate(start_point, start_tangent), translate(end_point, end_tangent), end_point)
        curve = AtomicNurbsCurve(controls, (1.0, 1.0, 1.0, 1.0), (0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0), 3)
        return curve, curve_length(curve), AtomicInterval(0.0, 1.0)
