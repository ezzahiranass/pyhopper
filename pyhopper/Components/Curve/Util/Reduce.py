"""Reduce - Reduce a polyline by removing least significant vertices (Grasshopper "Reduce")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicPolyline
from pyhopper.Utils.CurveEditing import polyline_points, reduce_polyline
from pyhopper.Core.TypeSystem import CURVE


class Reduce(Component):
    """Reduce a polyline by removing least significant vertices.

    Inputs:
        polyline: Polyline to reduce (Grasshopper Polyline [item]).
        tolerance: Tolerance (allowed deviation between original and reduction) (Grasshopper Tolerance [item]).

    Outputs:
        polyline: Reduced polyline (Grasshopper Polyline).
        reduction: Number of vertices removed during reduction (Grasshopper Reduction).

    Notes:
        Grasshopper: Curve > Util > Reduce (RedPLine).
        pyhopper decisions: Grasshopper-verified — Douglas-Peucker: vertices within the tolerance of
        the chord of their run are removed, the farthest vertex of each run is kept, the end points
        (and a closing duplicate) always stay; the reduction is the number of vertices removed.
        Default tolerance 1.
    """

    display_name = "Reduce"
    nickname = "RedPLine"
    gh_guid = "884646c3-0e70-4ad1-90c5-42601ee26450"

    inputs = [
        InputParam("polyline", CURVE, Access.ITEM),
        InputParam("tolerance", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("polyline", CURVE),
        OutputParam("reduction", int),
    ]

    def generate(self, polyline=None, tolerance=1.0):
        points, removed = reduce_polyline(polyline_points(polyline), float(tolerance))
        return AtomicPolyline(tuple(points)), removed
