"""RebuildCurve - Rebuild a curve with a specific number of control-points (Grasshopper "Rebuild Curve")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveFitting import rebuild_curve
from pyhopper.Core.TypeSystem import CURVE


class RebuildCurve(Component):
    """Rebuild a curve with a specific number of control-points.

    Inputs:
        curve: Curve to rebuild (Grasshopper Curve [item]).
        degree: Optional degree of curve (if omitted, input degree is used) (Grasshopper Degree [item]).
        count: Number of control points (Grasshopper Count [item]).
        tangents: Preserve curve end tangents (Grasshopper Tangents [item]).

    Outputs:
        curve: Rebuild curve (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Util > Rebuild Curve (ReB).
        pyhopper decisions: a least-squares fit of ``count`` control points with Rhino-style uniform
        clamped knots, the ends pinned and, with ``tangents``, the neighbouring control points sliding
        along the end tangents; ``degree`` defaults to the curve's own. Rhino's rebuild samples
        differently, so control points agree only for simple cases — structure (count, degree, knots)
        always does. Too few control points for the degree raise ``ValueError``.
    """

    display_name = "Rebuild Curve"
    nickname = "ReB"
    gh_guid = "9333c5b3-11f9-423c-bbb5-7e5156430219"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("degree", int, Access.ITEM, optional=True),
        InputParam("count", int, Access.ITEM, default=10),
        InputParam("tangents", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("curve", CURVE),
    ]

    def generate(self, curve=None, degree=None, count=10, tangents=False):
        return rebuild_curve(curve, int(count), None if degree is None else int(degree), bool(tangents))
