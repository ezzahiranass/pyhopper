"""PolylineCollapse - Collapse short segments in a polyline curve (Grasshopper "Polyline Collapse")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicPolyline
from pyhopper.Utils.CurveEditing import collapse_short_segments, polyline_points
from pyhopper.Core.TypeSystem import CURVE


class PolylineCollapse(Component):
    """Collapse short segments in a polyline curve.

    Inputs:
        polyline: Polyline curve (Grasshopper Polyline [item]).
        tolerance: Segment length tolerance (Grasshopper Tolerance [item]).

    Outputs:
        polyline: Resulting polyline (Grasshopper Polyline).
        count: Number of segments that were collapsed (Grasshopper Count).

    Notes:
        Grasshopper: Curve > Util > Polyline Collapse (PCol).
        pyhopper decisions: Grasshopper-verified — the shortest segment is collapsed first and the
        search repeats while the shortest segment is shorter than the tolerance: interior pairs merge
        into their midpoint, a segment touching an end keeps the end point, and a polyline never drops
        below two points. Polylines, lines and degree-1 NURBS are accepted. Default tolerance 1.
    """

    display_name = "Polyline Collapse"
    nickname = "PCol"
    gh_guid = "be298882-28c9-45b1-980d-7192a531c9a9"

    inputs = [
        InputParam("polyline", CURVE, Access.ITEM),
        InputParam("tolerance", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("polyline", CURVE),
        OutputParam("count", int),
    ]

    def generate(self, polyline=None, tolerance=1.0):
        points, count = collapse_short_segments(polyline_points(polyline), float(tolerance))
        return AtomicPolyline(tuple(points)), count
