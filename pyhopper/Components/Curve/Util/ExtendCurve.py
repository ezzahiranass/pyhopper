"""ExtendCurve - Extend a curve by a specified distance (Grasshopper "Extend Curve")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import extend_curve
from pyhopper.Core.TypeSystem import CURVE


class ExtendCurve(Component):
    """Extend a curve by a specified distance.

    Inputs:
        curve: Curve to extend (Grasshopper Curve [item]).
        type: Type of extension (0=Line, 1=Arc, 2=Smooth) (Grasshopper Type [item]).
        start: Extension length at start of curve (Grasshopper Start [item]).
        end: Extension length at end of curve (Grasshopper End [item]).

    Outputs:
        curve: Extended curve (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Util > Extend Curve (Ext).
        pyhopper decisions: Grasshopper-verified — type 0 (and unknown types) appends straight lines,
        1 arcs with the end curvature (a line where the curve is straight), 2 extends the curve itself
        (lines and polylines grow, arcs sweep further, NURBS curves extrapolate their end spans by the
        requested arc length); negative lengths trim by arc length; closed curves are unchanged.
        Extension pieces get Rhino's parameter span ``length / speed``. Grasshopper has no default
        lengths; pyhopper's 0 leaves the curve alone.
    """

    display_name = "Extend Curve"
    nickname = "Ext"
    gh_guid = "62cc9684-6a39-422e-aefa-ed44643557b9"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("type", int, Access.ITEM, default=0),
        InputParam("start", float, Access.ITEM, default=0.0),
        InputParam("end", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("curve", CURVE),
    ]

    def generate(self, curve=None, type=0, start=0.0, end=0.0):
        return extend_curve(curve, int(type), float(start), float(end))
