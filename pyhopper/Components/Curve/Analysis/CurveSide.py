"""CurveSide - Find on which side of a curve a point exists (Grasshopper "Curve Side")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import curve_side
from pyhopper.Core.TypeSystem import CURVE


class CurveSide(Component):
    """Find on which side of a curve a point exists.

    Inputs:
        curve: Base curve (Grasshopper Curve [item]).
        point: Point to measure. (Grasshopper Point [item]).
        plane: Optional plane to measure in. If omitted, the curve plane will be used. (Grasshopper Plane [item]).

    Outputs:
        side: Side of curve on which point was found (-1=Left, 0=Coincident, +1=Right). (Grasshopper Side).
        left: Boolean indicating whether a point is to the left of the curve. (Grasshopper Left).
        right: Boolean indicating whether a point is to the right of the curve. (Grasshopper Right).

    Notes:
        Grasshopper: Curve > Analysis > Curve Side (Side).
        pyhopper decisions: Grasshopper-verified — -1 (left) when ``(tangent × (point − closest)) ·
        normal`` is positive at the closest point, +1 (right) when negative, 0 within tolerance of the
        curve; the Left/Right flags follow. Without a plane arcs and circles use their own plane, other
        planar curves a fitted plane whose normal points towards +z (Rhino's canonical fit), lines and
        non-planar curves World XY. coincidence uses pyhopper's absolute tolerance (0.01, Rhino's default document tolerance that Grasshopper uses).
    """

    display_name = "Curve Side"
    nickname = "Side"
    gh_guid = "bb2e13da-09ca-43fd-bef8-8d71f3653af9"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("plane", AtomicPlane, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("side", int),
        OutputParam("left", bool),
        OutputParam("right", bool),
    ]

    def generate(self, curve=None, point=AtomicPoint.origin(), plane=None):
        side = curve_side(curve, point, plane)
        return side, side < 0, side > 0
