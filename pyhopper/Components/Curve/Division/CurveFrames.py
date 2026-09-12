"""CurveFrames - Generate a number of equally spaced curve frames (Grasshopper "Curve Frames")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import divide_curve_by_count
from pyhopper.Utils.Differential import curve_analysis, frenet_frame
from pyhopper.Core.TypeSystem import CURVE


class CurveFrames(Component):
    """Generate a number of equally spaced curve frames.

    Inputs:
        curve: Curve to divide (Grasshopper Curve [item]).
        count: Number of segments (Grasshopper Count [item]).

    Outputs:
        frames: Curve frames (Grasshopper Frames).
        parameters: Parameter values at division points (Grasshopper Parameters).

    Notes:
        Grasshopper: Curve > Division > Curve Frames (Frames).
        pyhopper decisions: Grasshopper-verified — ``count`` equal-length segments give ``count + 1``
        curvature frames (see Curve Frame) with their native parameters; a count below one raises
        ``ValueError``. Default 10.
    """

    display_name = "Curve Frames"
    nickname = "Frames"
    gh_guid = "0e94542a-2e46-4793-9f98-2200b06b28f4"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("count", int, Access.ITEM, default=10),
    ]
    outputs = [
        OutputParam("frames", AtomicPlane, access=Access.LIST),
        OutputParam("parameters", float, access=Access.LIST),
    ]

    def generate(self, curve=None, count=10):
        _, _, parameters = divide_curve_by_count(curve, int(count))
        return [frenet_frame(curve_analysis(curve, t)) for t in parameters], parameters
