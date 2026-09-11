"""ControlPoints - Extract the nurbs control points and knots of a curve (Grasshopper "Control Points")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Nurbs import rhino_knots
from pyhopper.Core.TypeSystem import CURVE


class ControlPoints(Component):
    """Extract the nurbs control points and knots of a curve.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).

    Outputs:
        points: Control points of the Nurbs-form. (Grasshopper Points).
        weights: Weights of control points. (Grasshopper Weights).
        knots: Knot vector of Nurbs-form. (Grasshopper Knots).

    Notes:
        Grasshopper: Curve > Analysis > Control Points (CP).
        pyhopper decisions: named curve atoms are converted to their NURBS form first (circles become the 9-point
        rational quadratic); ``knots`` uses Rhino's convention without the two superfluous end knots,
        scaled to the [0, 1] domain of pyhopper's native curves.
    """

    display_name = "Control Points"
    nickname = "CP"
    gh_guid = "424eb433-2b3a-4859-beaf-804d8af0afd7"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("weights", float, access=Access.LIST),
        OutputParam("knots", float, access=Access.LIST),
    ]

    def generate(self, curve=None):
        from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
        nurbs = as_nurbs_curve(curve)
        return list(nurbs.control_points), [float(weight) for weight in nurbs.weights], list(rhino_knots(nurbs.knots))
