"""CurveSelf - Solve all self intersection events for a curve (Grasshopper "Curve | Self")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Intersections import curve_self_intersections


class CurveSelf(Component):
    """Solve all self intersection events for a curve.

    Inputs:
        curve: Curve for self-intersections (Grasshopper Curve [item]).

    Outputs:
        points: Intersection events (Grasshopper Points).
        params: Parameters on curve (Grasshopper Params).

    Notes:
        Grasshopper: Intersect > Physical > Curve | Self (CX).
        pyhopper decisions: Grasshopper-verified — every self-intersection is listed twice: first all events
        with their first (smaller) parameter, then all events again with their second parameter, so
        ``points`` repeats and ``params`` holds ``[t1, t2, ..., t1', t2', ...]``. Events are sorted by the
        first parameter; the seam of a closed curve is not a self-intersection. Coincidence uses pyhopper's
        absolute tolerance (0.01, Rhino's default document tolerance that Grasshopper uses).
    """

    display_name = "Curve | Self"
    nickname = "CX"
    gh_guid = "0991ac99-6a0b-47a9-b07d-dd510ca57f0f"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("params", float, access=Access.LIST),
    ]

    def generate(self, curve=None):
        events = curve_self_intersections(curve)
        points = [point for _, _, point in events]
        return points + points, [ta for ta, _, _ in events] + [tb for _, tb, _ in events]
