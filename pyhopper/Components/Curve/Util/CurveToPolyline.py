"""CurveToPolyline - Convert a curve to a polyline (Grasshopper "Curve To Polyline")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveFitting import curve_to_polyline
from pyhopper.Core.TypeSystem import CURVE


class CurveToPolyline(Component):
    """Convert a curve to a polyline.

    Inputs:
        curve: Curve to simplify (Grasshopper Curve [item]).
        tolerance_distance: Deviation tolerance (Grasshopper Tolerance (distance) [item]).
        tolerance_angle: Angle tolerance in radians (Grasshopper Tolerance (angle) [item]).
        min_edge: Optional minimum allowed segment length (Grasshopper MinEdge [item]).
        max_edge: Optional maximum allowed segment length (Grasshopper MaxEdge [item]).

    Outputs:
        polyline: Converted curve (Grasshopper Polyline).
        segments: Number of polyline segments (Grasshopper Segments).

    Notes:
        Grasshopper: Curve > Util > Curve To Polyline (ToPoly).
        pyhopper decisions: lines and polylines pass through; arcs and circles use the smallest segment
        count whose chord sagitta is within the distance tolerance, then more segments for ``max_edge``
        and fewer for ``min_edge`` (reproduces Grasshopper's counts); other curves are bisected until
        every chord's midpoint deviation is within the tolerance. A tolerance of 0 (Grasshopper's
        default) means 0.001; the angle tolerance is accepted but not used.
    """

    display_name = "Curve To Polyline"
    nickname = "ToPoly"
    gh_guid = "2956d989-3599-476f-bc92-1d847aff98b6"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("tolerance_distance", float, Access.ITEM, default=0.0),
        InputParam("tolerance_angle", float, Access.ITEM, default=0.0),
        InputParam("min_edge", float, Access.ITEM, optional=True),
        InputParam("max_edge", float, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("polyline", CURVE),
        OutputParam("segments", int),
    ]

    def generate(self, curve=None, tolerance_distance=0.0, tolerance_angle=0.0, min_edge=None, max_edge=None):
        polyline = curve_to_polyline(curve, float(tolerance_distance), float(tolerance_angle), None if min_edge is None else float(min_edge), None if max_edge is None else float(max_edge))
        return polyline, len(polyline.points) - 1
