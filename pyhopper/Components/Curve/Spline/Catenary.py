"""Catenary - Create a catenary chain between two points (Grasshopper "Catenary")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicLine, AtomicPolyline
from pyhopper.Utils.CurveFitting import catenary_points
from pyhopper.Core.TypeSystem import CURVE


class Catenary(Component):
    """Create a catenary chain between two points.

    Inputs:
        point_a: Start point of catenary (Grasshopper Point A [item]).
        point_b: End point of catenary (Grasshopper Point B [item]).
        length: Length of catenary chain (should be larger than the distance |AB|) (Grasshopper Length [item]).
        gravity: Direction of gravity (Grasshopper Gravity [item]).

    Outputs:
        catenary: Catenary chain (Grasshopper Catenary).

    Notes:
        Grasshopper: Curve > Spline > Catenary (Cat).
        pyhopper decisions: the exact catenary sampled at 50 points spaced uniformly along the
        horizontal span, returned as a polyline like Grasshopper; a chain no longer than the distance
        between the points is taut and comes back as the straight line (Grasshopper warns); a purely
        vertical span raises ``ValueError``. Gravity defaults to -Z.
    """

    display_name = "Catenary"
    nickname = "Cat"
    gh_guid = "275671d4-3e87-40bd-8aff-8e6a5fdbb892"

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("point_b", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("length", float, Access.ITEM, default=0.0),
        InputParam("gravity", AtomicVector, Access.ITEM, default=AtomicVector(0.0, 0.0, -1.0)),
    ]
    outputs = [
        OutputParam("catenary", CURVE),
    ]

    def generate(self, point_a=AtomicPoint.origin(), point_b=AtomicPoint.origin(), length=0.0, gravity=AtomicVector(0.0, 0.0, -1.0)):
        points = catenary_points(point_a, point_b, float(length), gravity)
        if points is None:
            return AtomicLine(point_a, point_b)
        return AtomicPolyline(tuple(points))
