"""InterpolateT - Create an interpolated curve through a set of points with tangents (Grasshopper "Interpolate (t)")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_length
from pyhopper.Utils.Interpolation import rhino_interpolated_curve
from pyhopper.Core.TypeSystem import CURVE


class InterpolateT(Component):
    """Create an interpolated curve through a set of points with tangents.

    Inputs:
        vertices: Interpolation points (Grasshopper Vertices [list]).
        tangent_start: Tangent at start of curve (Grasshopper Tangent Start [item]).
        tangent_end: Tangent at end of curve (Grasshopper Tangent End [item]).
        knot_style: Knot spacing (0=uniform, 1=chord, 2=sqrtchord) (Grasshopper KnotStyle [item]).

    Outputs:
        curve: Resulting nurbs curve (Grasshopper Curve).
        length: Curve length (Grasshopper Length).
        domain: Curve domain (Grasshopper Domain).

    Notes:
        Grasshopper: Curve > Spline > Interpolate (t) (IntCrv(t)).
        pyhopper decisions: Grasshopper-verified — Rhino's interpolation: a clamped cubic with two
        extra control points a third of the first/last chord along the tangents; a zero tangent
        (the default) is replaced by the direction of the parabola through the three end points, and
        two points give a single Bezier whose handles follow the circular-arc rule. Knot style 0/1/2 =
        uniform/chord/square-root chord (default chord); length and domain follow the curve.
    """

    display_name = "Interpolate (t)"
    nickname = "IntCrv(t)"
    gh_guid = "75eb156d-d023-42f9-a85e-2f2456b8bcce"

    inputs = [
        InputParam("vertices", AtomicPoint, Access.LIST),
        InputParam("tangent_start", AtomicVector, Access.ITEM, default=AtomicVector(0.0, 0.0, 0.0)),
        InputParam("tangent_end", AtomicVector, Access.ITEM, default=AtomicVector(0.0, 0.0, 0.0)),
        InputParam("knot_style", int, Access.ITEM, default=1),
    ]
    outputs = [
        OutputParam("curve", CURVE),
        OutputParam("length", float),
        OutputParam("domain", AtomicInterval),
    ]

    def generate(self, vertices=None, tangent_start=AtomicVector(0.0, 0.0, 0.0), tangent_end=AtomicVector(0.0, 0.0, 0.0), knot_style=1):
        curve = rhino_interpolated_curve(list(vertices or []), int(knot_style), tangent_start, tangent_end)
        return curve, curve_length(curve), AtomicInterval(curve.knots[3], curve.knots[-4])
