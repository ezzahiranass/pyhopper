"""ConnectCurves - Connect a sequence of curves (Grasshopper "Connect Curves")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import connect_curves
from pyhopper.Core.TypeSystem import CURVE


class ConnectCurves(Component):
    """Connect a sequence of curves.

    Inputs:
        curves: Curves to connect (Grasshopper Curves [list]).
        continuity: Continuity of blends (0=position, 1=tangency, 2=curvature) (Grasshopper Continuity [item]).
        close: Create a closed loop from all curves (Grasshopper Close [item]).
        bulge: Bulge factor for connecting segments (Grasshopper Bulge [item]).

    Outputs:
        curve: Joined segments and connecting curves (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Spline > Connect Curves (Connect).
        pyhopper decisions: Grasshopper-verified — the curves in order, joined by Blend Curve blends
        (equal bulges) wherever consecutive ends do not touch, optionally closed with a blend back to
        the start; a single unclosed curve comes back as it is. Defaults: continuity 2, close on,
        bulge 1.
    """

    display_name = "Connect Curves"
    nickname = "Connect"
    gh_guid = "d0a1b843-873d-4d1d-965c-b5423b35f327"

    inputs = [
        InputParam("curves", CURVE, Access.LIST),
        InputParam("continuity", int, Access.ITEM, default=2),
        InputParam("close", bool, Access.ITEM, default=True),
        InputParam("bulge", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("curve", CURVE),
    ]

    def generate(self, curves=None, continuity=2, close=True, bulge=1.0):
        return connect_curves(list(curves or []), int(continuity), bool(close), float(bulge))
