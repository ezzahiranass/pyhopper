"""PointInCurves - Test a point for multiple closed curve containment (Grasshopper "Point in Curves")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import point_in_closed_curve
from pyhopper.Core.TypeSystem import CURVE


class PointInCurves(Component):
    """Test a point for multiple closed curve containment.

    Inputs:
        point: Point for inclusion test (Grasshopper Point [item]).
        curves: Boundary regions (closed curves only) (Grasshopper Curves [list]).

    Outputs:
        relationship: Point/Region relationship (0 = outside, 1 = coincident, 2 = inside) (Grasshopper Relationship).
        index: Index of first region that contains the point (Grasshopper Index).
        point: Point projected on region plane. (Grasshopper Point).

    Notes:
        Grasshopper: Curve > Analysis > Point in Curves (InCurves).
        pyhopper decisions: Grasshopper-verified — the first curve (in list order) the point is inside
        or on decides: its relationship (1 coincident, 2 inside), its index and the point projected onto
        its plane; outside every curve gives 0, -1 and the point itself. Open curves are skipped. coincidence uses pyhopper's absolute tolerance (0.01, Rhino's default document tolerance that Grasshopper uses).
    """

    display_name = "Point in Curves"
    nickname = "InCurves"
    gh_guid = "0b04e8b9-00d7-47a7-95c3-0d51e654fe88"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("curves", CURVE, Access.LIST),
    ]
    outputs = [
        OutputParam("relationship", int),
        OutputParam("index", int),
        OutputParam("point", AtomicPoint),
    ]

    def generate(self, point=AtomicPoint.origin(), curves=None):
        for index, curve in enumerate(curves or []):
            try:
                relationship, projected = point_in_closed_curve(curve, point)
            except ValueError:
                continue
            if relationship:
                return relationship, index, projected
        return 0, -1, point
