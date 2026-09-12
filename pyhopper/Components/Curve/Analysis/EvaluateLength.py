"""EvaluateLength - Evaluate a curve at a certain factor along its length. Length factors can be supplied both in curve units and normalized units. Change the [N] parameter to toggle between the two modes (Grasshopper "Evaluate Length")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_length, curve_parameter_at_length, curve_point_at, curve_tangent_at
from pyhopper.Core.TypeSystem import CURVE


class EvaluateLength(Component):
    """Evaluate a curve at a certain factor along its length. Length factors can be supplied both in curve units and normalized units. Change the [N] parameter to toggle between the two modes.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).
        length: Length factor for curve evaluation (Grasshopper Length [item]).
        normalized: If True, the Length factor is normalized (0.0 ~ 1.0) (Grasshopper Normalized [item]).

    Outputs:
        point: Point at the specified length (Grasshopper Point).
        tangent: Tangent vector at the specified length (Grasshopper Tangent).
        parameter: Curve parameter at the specified length (Grasshopper Parameter).

    Notes:
        Grasshopper: Curve > Analysis > Evaluate Length (Eval).
        pyhopper decisions: ``length`` is a fraction of the curve length when ``normalized`` (the
        default) or an absolute length otherwise; values outside the curve raise ``ValueError`` where
        Grasshopper emits nulls. The parameter is the curve's native one (see Evaluate Curve).
    """

    display_name = "Evaluate Length"
    nickname = "Eval"
    gh_guid = "6b021f56-b194-4210-b9a1-6cef3b7d0848"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("length", float, Access.ITEM, default=0.0),
        InputParam("normalized", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("tangent", AtomicVector),
        OutputParam("parameter", float),
    ]

    def generate(self, curve=None, length=0.0, normalized=True):
        total = curve_length(curve)
        distance_along = float(length) * total if normalized else float(length)
        if distance_along < -1e-12 or distance_along > total + 1e-12:
            raise ValueError("EvaluateLength needs a length within the curve" if not normalized else "EvaluateLength needs a normalized length between 0 and 1")
        parameter = curve_parameter_at_length(curve, min(max(distance_along, 0.0), total))
        return curve_point_at(curve, parameter), curve_tangent_at(curve, parameter), parameter
