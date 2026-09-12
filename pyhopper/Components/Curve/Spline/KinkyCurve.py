"""KinkyCurve - Construct an interpolated curve through a set of points with a kink angle threshold (Grasshopper "Kinky Curve")."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicInterval, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_length
from pyhopper.Utils.Interpolation import kinky_curve
from pyhopper.Core.TypeSystem import CURVE


class KinkyCurve(Component):
    """Construct an interpolated curve through a set of points with a kink angle threshold.

    Inputs:
        vertices: Interpolation points (Grasshopper Vertices [list]).
        degree: Curve degree (Grasshopper Degree [item]).
        angle: Kink angle threshold (in radians) (Grasshopper Angle [item]).

    Outputs:
        curve: Resulting nurbs curve (Grasshopper Curve).
        length: Curve length (Grasshopper Length).
        domain: Curve domain (Grasshopper Domain).

    Notes:
        Grasshopper: Curve > Spline > Kinky Curve (KinkCrv).
        pyhopper decisions: Grasshopper-verified — vertices where the polyline turns by more than the
        angle (default 10 degrees) are kinks; runs of two vertices become lines (knot span = length),
        longer runs are interpolated with uniform knots (degree 1: the polyline, degree 3: Rhino's
        interpolation) and the pieces join with full-multiplicity knots, lines being raised to the
        curve degree. Degrees other than 1 and 3 raise ``ValueError``.
    """

    display_name = "Kinky Curve"
    nickname = "KinkCrv"
    gh_guid = "6f0993e8-5f2f-4fc0-bd73-b84bc240e78e"

    inputs = [
        InputParam("vertices", AtomicPoint, Access.LIST),
        InputParam("degree", int, Access.ITEM, default=3),
        InputParam("angle", float, Access.ITEM, default=math.radians(10.0)),
    ]
    outputs = [
        OutputParam("curve", CURVE),
        OutputParam("length", float),
        OutputParam("domain", AtomicInterval),
    ]

    def generate(self, vertices=None, degree=3, angle=math.radians(10.0)):
        curve = kinky_curve(list(vertices or []), int(degree), float(angle))
        return curve, curve_length(curve), AtomicInterval(curve.knots[curve.degree], curve.knots[-curve.degree - 1])
