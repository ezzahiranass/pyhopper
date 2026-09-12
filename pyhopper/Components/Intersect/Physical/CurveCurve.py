"""CurveCurve - Solve intersection events for two curves (Grasshopper "Curve | Curve")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Intersections import curve_curve_intersections


class CurveCurve(Component):
    """Solve intersection events for two curves.

    Inputs:
        curve_a: First curve (Grasshopper Curve A [item]).
        curve_b: Second curve (Grasshopper Curve B [item]).

    Outputs:
        points: Intersection events (Grasshopper Points).
        params_a: Parameters on first curve (Grasshopper Params A).
        params_b: Parameters on second curve (Grasshopper Params B).

    Notes:
        Grasshopper: Intersect > Physical > Curve | Curve (CCX).
        pyhopper decisions: Grasshopper-verified — crossings and touches within tolerance sorted along curve
        A, each point the midpoint of the two curve points; a collinear overlap of straight pieces reports
        its two ends; a closed curve's seam counts once (at its start parameter). Parameters are the curves'
        native ones (reparametrize the inputs for [0, 1]). Coincidence uses pyhopper's absolute tolerance
        (0.01, Rhino's default document tolerance that Grasshopper uses).
    """

    display_name = "Curve | Curve"
    nickname = "CCX"
    gh_guid = "84627490-0fb2-4498-8138-ad134ee4cb36"

    inputs = [
        InputParam("curve_a", CURVE, Access.ITEM),
        InputParam("curve_b", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("params_a", float, access=Access.LIST),
        OutputParam("params_b", float, access=Access.LIST),
    ]

    def generate(self, curve_a=None, curve_b=None):
        events = curve_curve_intersections(curve_a, curve_b)
        return [point for _, _, point in events], [ta for ta, _, _ in events], [tb for _, tb, _ in events]
