"""FilletDistance - Fillet the sharp corners of a curve by distance (Grasshopper "Fillet Distance")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import fillet_distance
from pyhopper.Core.TypeSystem import CURVE


class FilletDistance(Component):
    """Fillet the sharp corners of a curve by distance.

    Inputs:
        curve: Curve to fillet (Grasshopper Curve [item]).
        distance: Distance from corner of fillet start (Grasshopper Distance [item]).

    Outputs:
        curve: Curve with filleted corners (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Util > Fillet Distance (Fillet).
        pyhopper decisions: Grasshopper-verified — every polyline corner is rounded with an arc whose
        tangent points sit ``distance`` from the corner; the result is lines and arcs on natural spans
        (a closed polyline starts with the arc at its seam). A distance larger than half an interior
        edge is clamped on that side (Grasshopper keeps the longer side and draws a conic); zero
        returns the curve, a negative distance raises ``ValueError`` (Grasshopper reports an error), a
        distance that does not fit an end edge wraps the curve in a polycurve as Grasshopper does.
    """

    display_name = "Fillet Distance"
    nickname = "Fillet"
    gh_guid = "6fb21315-a032-400e-a80f-248687f5507f"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("distance", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("curve", CURVE),
    ]

    def generate(self, curve=None, distance=0.0):
        return fillet_distance(curve, float(distance))
