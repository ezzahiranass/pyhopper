"""PullCurve - Pull a curve onto a surface (Grasshopper "Pull Curve")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurvesOnSurfaces import pull_curve
from pyhopper.Core.TypeSystem import CURVE, SURFACE


class PullCurve(Component):
    """Pull a curve onto a surface.

    Inputs:
        curve: Curve to pull (Grasshopper Curve [item]).
        surface: Surface that pulls (Grasshopper Surface [item]).

    Outputs:
        curve: Curve pulled onto the surface (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Util > Pull Curve (Pull).
        pyhopper decisions: Grasshopper-verified in structure — samples are moved to their closest
        surface points, stretches whose normal projection misses the surface are dropped and the runs
        interpolated (straight runs become lines); a curve already on the surface comes back unchanged.
        Rhino refits its own curve, so only the structure compares.
    """

    display_name = "Pull Curve"
    nickname = "Pull"
    gh_guid = "8db16e9c-2816-4c95-939d-8fecdc30906f"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("surface", SURFACE, Access.ITEM),
    ]
    outputs = [
        OutputParam("curve", CURVE, access=Access.LIST),
    ]

    def generate(self, curve=None, surface=None):
        return pull_curve(curve, surface)
