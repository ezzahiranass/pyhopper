"""ControlPolygon - Extract the nurbs control polygon of a curve (Grasshopper "Control Polygon")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicPolyline
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Core.TypeSystem import CURVE


class ControlPolygon(Component):
    """Extract the nurbs control polygon of a curve.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).

    Outputs:
        polygon: Control polygon curve for input curve adjusted for periodicity. (Grasshopper Polygon).
        points: Control polygon points. (Grasshopper Points).

    Notes:
        Grasshopper: Curve > Analysis > Control Polygon (CPoly).
        pyhopper decisions: the control points of the curve's NURBS form (arcs and circles give their
        rational control points, polylines their vertices) as a polyline plus the point list, as in
        Grasshopper.
    """

    display_name = "Control Polygon"
    nickname = "CPoly"
    gh_guid = "66d2a68e-2f1d-43d2-a53b-c6a4d17e627b"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("polygon", CURVE),
        OutputParam("points", AtomicPoint, access=Access.LIST),
    ]

    def generate(self, curve=None):
        points = list(as_nurbs_curve(curve).control_points)
        return AtomicPolyline(tuple(points)), points
