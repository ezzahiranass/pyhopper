"""Fillet - Fillet a curve at a parameter (Grasshopper "Fillet")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import fillet_at
from pyhopper.Core.TypeSystem import CURVE


class Fillet(Component):
    """Fillet a curve at a parameter.

    Inputs:
        curve: Curve to fillet (Grasshopper Curve [item]).
        parameter: Curve parameter for fillet (Grasshopper Parameter [item]).
        radius: Radius of fillet (Grasshopper Radius [item]).

    Outputs:
        curve: Filleted curve (Grasshopper Curve).
        parameter: Parameter where the fillet eventually occured (Grasshopper Parameter).

    Notes:
        Grasshopper: Curve > Util > Fillet (Fillet).
        pyhopper decisions: Grasshopper-verified — the polyline corner nearest to the parameter (the
        seam counts on closed polylines) is replaced by an arc tangent to both edges; the pieces keep
        their parameter spans, the arc gets its length; on a closed polyline the single remaining piece
        runs through the seam and, for a corner other than the seam, follows the arc with the domain
        starting where the piece ends (Rhino's layout). The Parameter output is the corner's parameter.
        When there is no corner or the radius does not fit, the curve comes back unchanged with the
        input parameter (Grasshopper reports "Fillet failed"); a zero radius returns the curve and no
        parameter. Grasshopper has no default parameter or radius.
    """

    display_name = "Fillet"
    nickname = "Fillet"
    gh_guid = "c92cdfc8-3df8-4c4e-abc1-ede092a0aa8a"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameter", float, Access.ITEM, default=0.0),
        InputParam("radius", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("curve", CURVE),
        OutputParam("parameter", float),
    ]

    def generate(self, curve=None, parameter=0.0, radius=0.0):
        result, corner = fillet_at(curve, float(parameter), float(radius))
        return result, (Component.NO_OUTPUT if corner is None else corner)
