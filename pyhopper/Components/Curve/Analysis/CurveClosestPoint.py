"""CurveClosestPoint - Find the closest point on a curve (Grasshopper "Curve Closest Point")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import curve_closest_point
from pyhopper.Core.TypeSystem import CURVE


class CurveClosestPoint(Component):
    """Find the closest point on a curve.

    Inputs:
        point: Point to project onto curve (Grasshopper Point [item]).
        curve: Curve to project onto (Grasshopper Curve [item]).

    Outputs:
        point: Point on the curve closest to the base point (Grasshopper Point).
        parameter: Parameter on curve domain of closest point (Grasshopper Parameter).
        distance: Distance between base point and curve (Grasshopper Distance).

    Notes:
        Grasshopper: Curve > Analysis > Curve Closest Point (Crv CP).
        pyhopper decisions: Grasshopper-verified — closest point, its parameter (the curve's native
        parameterisation; use the Reparameterize port operation for [0, 1]) and the distance; lines,
        polylines, arcs and circles are solved analytically (a point on a circle's axis lands on the
        seam, a point opposite an arc's middle on its end, like Rhino), other curves by Newton
        refinement of sampled candidates.
    """

    display_name = "Curve Closest Point"
    nickname = "Crv CP"
    gh_guid = "2dc44b22-b1dd-460a-a704-6462d6e91096"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("curve", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("parameter", float),
        OutputParam("distance", float),
    ]

    def generate(self, point=AtomicPoint.origin(), curve=None):
        t, closest, d = curve_closest_point(curve, point)
        return closest, t, d
