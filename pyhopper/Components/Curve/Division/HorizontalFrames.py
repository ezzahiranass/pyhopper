"""HorizontalFrames - Generate a number of equally spaced, horizontally aligned curve frames (Grasshopper "Horizontal Frames")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import divide_curve_by_count
from pyhopper.Utils.Frames import horizontal_frame
from pyhopper.Core.TypeSystem import CURVE


class HorizontalFrames(Component):
    """Generate a number of equally spaced, horizontally aligned curve frames.

    Inputs:
        curve: Curve to divide (Grasshopper Curve [item]).
        count: Number of segments (Grasshopper Count [item]).

    Outputs:
        frames: Curvature frames (Grasshopper Frames).
        parameters: Parameter values at division points (Grasshopper Parameters).

    Notes:
        Grasshopper: Curve > Division > Horizontal Frames (HFrames).
        pyhopper decisions: the division points of Divide Curve (``count + 1`` frames on an open curve,
        ``count`` on a closed one) with horizontal frames at each — Grasshopper-verified; a count below
        1 raises ``ValueError``.
    """

    display_name = "Horizontal Frames"
    nickname = "HFrames"
    gh_guid = "8d058945-ce47-4e7c-82af-3269295d7890"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("count", int, Access.ITEM, default=10),
    ]
    outputs = [
        OutputParam("frames", AtomicPlane, access=Access.LIST),
        OutputParam("parameters", float, access=Access.LIST),
    ]

    def generate(self, curve=None, count=10):
        points, tangents, parameters = divide_curve_by_count(curve, int(count))
        return [horizontal_frame(point, tangent) for point, tangent in zip(points, tangents)], parameters
