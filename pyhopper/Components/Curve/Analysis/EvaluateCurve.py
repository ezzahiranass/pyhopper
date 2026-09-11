"""EvaluateCurve - Evaluate a curve at the specified parameter (Grasshopper "Evaluate Curve")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_kink_angle, curve_point_at, curve_tangent_at
from pyhopper.Core.TypeSystem import CURVE


class EvaluateCurve(Component):
    """Evaluate a curve at the specified parameter.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).
        parameter: Parameter on curve domain to evaluate (Grasshopper Parameter [item]).

    Outputs:
        point: Point on the curve at {t} (Grasshopper Point).
        tangent: Tangent vector at {t} (Grasshopper Tangent).
        angle: Angle (in Radians) of incoming vs. outgoing curve at {t} (Grasshopper Angle).

    Notes:
        Grasshopper: Curve > Analysis > Evaluate Curve (Eval).
        pyhopper decisions: each curve kind keeps Grasshopper's parameterisation on [0, 1] (lines by length, polylines
        per segment, arcs by angle) and NURBS use their knots; ``angle`` is the kink angle between the
        incoming and outgoing tangents (0 on smooth spots), the tangent at a kink is the outgoing one.
    """

    display_name = "Evaluate Curve"
    nickname = "Eval"
    gh_guid = "fc6979e4-7e91-4508-8e05-37c680779751"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameter", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("tangent", AtomicVector),
        OutputParam("angle", float),
    ]

    def generate(self, curve=None, parameter=0.0):
        return curve_point_at(curve, parameter), curve_tangent_at(curve, parameter), curve_kink_angle(curve, parameter)
