"""PerpFrames - Generate a number of equally spaced, perpendicular frames along a curve (Grasshopper "Perp Frames")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import divide_curve_by_count
from pyhopper.Utils.Frames import curve_perpendicular_frames
from pyhopper.Core.TypeSystem import CURVE


class PerpFrames(Component):
    """Generate a number of equally spaced, perpendicular frames along a curve.

    Inputs:
        curve: Curve to divide (Grasshopper Curve [item]).
        count: Number of segments (Grasshopper Count [item]).
        align: Align the frames (Grasshopper Align [item]).

    Outputs:
        frames: Curve frames (Grasshopper Frames).
        parameters: Parameter values at frame points (Grasshopper Parameters).

    Notes:
        Grasshopper: Curve > Division > Perp Frames (PFrames).
        pyhopper decisions: frames at equal arc-length divisions with Z along the tangent; ``align`` sweeps a
        rotation-minimising frame from the curvature direction at the start (Rhino's
        GetPerpendicularFrames, converged), otherwise every frame takes Rhino's default X axis for
        its tangent; a count below 1 emits empty lists. Grasshopper defaults ``count = 10``,
        ``align = True``.
    """

    display_name = "Perp Frames"
    nickname = "PFrames"
    gh_guid = "983c7600-980c-44da-bc53-c804067f667f"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("count", int, Access.ITEM, default=10),
        InputParam("align", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("frames", AtomicPlane, access=Access.LIST),
        OutputParam("parameters", float, access=Access.LIST),
    ]

    def generate(self, curve=None, count=10, align=True):
        if int(count) < 1:
            return [], []
        _, _, parameters = divide_curve_by_count(curve, int(count))
        return curve_perpendicular_frames(curve, parameters, bool(align)), parameters
