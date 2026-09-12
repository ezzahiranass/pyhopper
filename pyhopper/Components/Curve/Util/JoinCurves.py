"""JoinCurves - Join as many curves as possible (Grasshopper "Join Curves")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import join_curves
from pyhopper.Core.TypeSystem import CURVE


class JoinCurves(Component):
    """Join as many curves as possible.

    Inputs:
        curves: Curves to join (Grasshopper Curves [list]).
        preserve: Preserve direction of input curves (Grasshopper Preserve [item]).

    Outputs:
        curves: Joined curves and individual curves that could not be joined. (Grasshopper Curves).

    Notes:
        Grasshopper: Curve > Util > Join Curves (Join).
        pyhopper decisions: Grasshopper-verified — chains start with the first unused curve; a candidate
        is prepended when its end meets the chain start, appended when its start meets the chain end,
        and (unless ``preserve``) flipped to fit start-to-start or end-to-end — chains of straight
        pieces flip themselves instead, as Rhino does while merging polylines. Chains of lines and
        polylines become one polyline, mixed chains a polycurve on natural spans whose domain starts
        where the first segment's does (minus its span when the join flipped it, Rhino's negated
        domain); lone curves stay as they are except lone lines, which Rhino hands back as two-point
        polylines unless ``preserve`` is on. The join tolerance is 1e-6.
    """

    display_name = "Join Curves"
    nickname = "Join"
    gh_guid = "8073a420-6bec-49e3-9b18-367f6fd76ac3"

    inputs = [
        InputParam("curves", CURVE, Access.LIST),
        InputParam("preserve", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("curves", CURVE, access=Access.LIST),
    ]

    def generate(self, curves=None, preserve=False):
        return join_curves(list(curves or []), bool(preserve))
