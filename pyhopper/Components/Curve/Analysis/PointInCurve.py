"""PointInCurve - Test a point for closed curve containment (Grasshopper "Point In Curve")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import point_in_closed_curve
from pyhopper.Core.TypeSystem import CURVE


class PointInCurve(Component):
    """Test a point for closed curve containment.

    Inputs:
        point: Point for region inclusion test (Grasshopper Point [item]).
        curve: Boundary region (closed curves only) (Grasshopper Curve [item]).

    Outputs:
        relationship: Point/Region relationship (0 = outside, 1 = coincident, 2 = inside) (Grasshopper Relationship).
        point: Point projected on region plane. (Grasshopper Point).

    Notes:
        Grasshopper: Curve > Analysis > Point In Curve (InCurve).
        pyhopper decisions: Grasshopper-verified — 0 outside, 1 coincident, 2 inside, judged in the
        curve's plane after projecting the point onto it (the projected point is the second output);
        open or non-planar curves raise ``ValueError`` (Grasshopper emits null with an error). coincidence uses pyhopper's absolute tolerance (0.01, Rhino's default document tolerance that Grasshopper uses).
    """

    display_name = "Point In Curve"
    nickname = "InCurve"
    gh_guid = "a72b0bd3-c7a7-458e-875d-09ae1624638c"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("curve", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("relationship", int),
        OutputParam("point", AtomicPoint),
    ]

    def generate(self, point=AtomicPoint.origin(), curve=None):
        return point_in_closed_curve(curve, point)
