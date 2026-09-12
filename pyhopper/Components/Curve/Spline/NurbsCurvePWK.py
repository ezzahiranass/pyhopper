"""NurbsCurvePWK - Construct a nurbs curve from control points, weights and knots (Grasshopper "Nurbs Curve PWK")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicNurbsCurve, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_length
from pyhopper.Utils.Nurbs import from_rhino_knots
from pyhopper.Core.TypeSystem import CURVE


class NurbsCurvePWK(Component):
    """Construct a nurbs curve from control points, weights and knots.

    Inputs:
        points: Curve control points (Grasshopper Points [list]).
        weights: Optional control point weights (Grasshopper Weights [list]).
        knots: Nurbs knot vector (Grasshopper Knots [list]).

    Outputs:
        curve: Resulting nurbs curve (Grasshopper Curve).
        length: Curve length (Grasshopper Length).
        domain: Curve domain (Grasshopper Domain).

    Notes:
        Grasshopper: Curve > Spline > Nurbs Curve PWK (NurbCrv).
        pyhopper decisions: the knots are Rhino-style (``count + degree - 1`` values), so the degree is
        ``len(knots) - len(points) + 1``; weights default to one; an impossible knot count raises
        ``ValueError`` (Grasshopper emits nulls). Length and domain follow the knots as given.
    """

    display_name = "Nurbs Curve PWK"
    nickname = "NurbCrv"
    gh_guid = "1f8e1ff7-8278-4421-b39d-350e71d85d37"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
        InputParam("weights", float, Access.LIST, optional=True),
        InputParam("knots", float, Access.LIST),
    ]
    outputs = [
        OutputParam("curve", CURVE),
        OutputParam("length", float),
        OutputParam("domain", AtomicInterval),
    ]

    def generate(self, points=None, weights=None, knots=None):
        controls = tuple(points or [])
        knot_list = [float(k) for k in (knots or [])]
        degree = len(knot_list) - len(controls) + 1
        if len(controls) < 2 or degree < 1 or degree >= len(controls):
            raise ValueError("NurbsCurvePWK needs count + degree - 1 knots for a valid degree")
        weight_list = tuple(float(w) for w in weights) if weights else tuple(1.0 for _ in controls)
        if len(weight_list) != len(controls):
            raise ValueError("NurbsCurvePWK needs one weight per control point")
        curve = AtomicNurbsCurve(controls, weight_list, from_rhino_knots(knot_list), degree)
        return curve, curve_length(curve), AtomicInterval(curve.knots[degree], curve.knots[len(controls)])
