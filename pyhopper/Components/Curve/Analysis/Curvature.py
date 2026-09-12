"""Curvature - Evaluate the curvature of a curve at a specified parameter (Grasshopper "Curvature")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Differential import curvature_circle, curve_analysis
from pyhopper.Core.TypeSystem import CURVE


class Curvature(Component):
    """Evaluate the curvature of a curve at a specified parameter.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).
        parameter: Parameter on curve domain to evaluate (Grasshopper Parameter [item]).

    Outputs:
        point: Point on curve at {t} (Grasshopper Point).
        curvature: Curvature vector at {t} (Grasshopper Curvature).
        circle: Curvature circle at {t} (Grasshopper Curvature).

    Notes:
        Grasshopper: Curve > Analysis > Curvature (Curvature).
        pyhopper decisions: Grasshopper-verified — the curvature vector ``k·n`` points towards the
        centre of curvature; the circle sits in the osculating plane with its x axis towards the point
        and its normal along the binormal; on a straight stretch the vector is zero and, like
        Grasshopper, a 200-long tangent line stands in for the infinite circle. ``parameter`` is the curve's native parameter (use the Reparameterize port operation for [0, 1]).
    """

    display_name = "Curvature"
    nickname = "Curvature"
    gh_guid = "aaa665bd-fd6e-4ccb-8d2c-c5b33072125d"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameter", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("curvature", AtomicVector),
        OutputParam("circle", CURVE),
    ]

    def generate(self, curve=None, parameter=0.0):
        analysis = curve_analysis(curve, float(parameter))
        return analysis.point, analysis.curvature_vector, curvature_circle(analysis)
