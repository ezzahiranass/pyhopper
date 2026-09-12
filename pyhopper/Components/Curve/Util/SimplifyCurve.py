"""SimplifyCurve - Simplify a curve (Grasshopper "Simplify Curve")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveEditing import simplify_curve
from pyhopper.Core.TypeSystem import CURVE


class SimplifyCurve(Component):
    """Simplify a curve.

    Inputs:
        curve: Curve to simplify (Grasshopper Curve [item]).
        tolerance: Optional deviation tolerance (if omitted, the current document tolerance is used) (Grasshopper Tolerance [item]).
        angle_tolerance: Optional angle tolerance (if omitted, the current document tolerance is used) (Grasshopper Angle Tolerance [item]).

    Outputs:
        curve: Simplified curve (Grasshopper Curve).
        simplified: True if curve was modified in any way (Grasshopper Simplified).

    Notes:
        Grasshopper: Curve > Util > Simplify Curve (Simplify).
        pyhopper decisions: Grasshopper-verified — polylines lose vertices where they turn by no more
        than the angle tolerance (and deviate no more than the tolerance), a single remaining segment
        becoming a line; NURBS with collinear control points become lines; other NURBS are left alone
        but reported as simplified (Rhino does the same); lines, circles and arcs are already simple.
        Omitted tolerances use Rhino's document defaults (0.001 units, 1 degree).
    """

    display_name = "Simplify Curve"
    nickname = "Simplify"
    gh_guid = "922dc7e5-0f0e-4c21-ae4b-f6a8654e63f6"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("tolerance", float, Access.ITEM, optional=True),
        InputParam("angle_tolerance", float, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("curve", CURVE),
        OutputParam("simplified", bool),
    ]

    def generate(self, curve=None, tolerance=None, angle_tolerance=None):
        distance_tolerance = 0.001 if tolerance is None else float(tolerance)
        turn_tolerance = math.radians(1.0) if angle_tolerance is None else float(angle_tolerance)
        return simplify_curve(curve, distance_tolerance, turn_tolerance)
