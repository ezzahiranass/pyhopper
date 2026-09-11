"""Closed - Test if a curve is closed or periodic (Grasshopper "Closed")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_is_closed, curve_is_periodic
from pyhopper.Core.TypeSystem import CURVE


class Closed(Component):
    """Test if a curve is closed or periodic.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).

    Outputs:
        closed: True if curve is closed or periodic (Grasshopper Closed).
        periodic: True if curve is periodic (Grasshopper Periodic).

    Notes:
        Grasshopper: Curve > Analysis > Closed (Cls).
        pyhopper decisions: ``periodic`` is true for circles and for closed NURBS curves with an unclamped knot vector
        (Rhino's notion); closed polylines are closed but not periodic, like Grasshopper.
    """

    display_name = "Closed"
    nickname = "Cls"
    gh_guid = "323f3245-af49-4489-8677-7a2c73664077"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("closed", bool),
        OutputParam("periodic", bool),
    ]

    def generate(self, curve=None):
        return curve_is_closed(curve), curve_is_periodic(curve)
