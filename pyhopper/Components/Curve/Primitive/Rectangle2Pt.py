"""Rectangle2Pt - Create a rectangle from a base plane and two points (Grasshopper "Rectangle 2Pt")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._rectangles import make_rectangle, rectangle_from_corners
from pyhopper.Core.TypeSystem import GEOMETRY


class Rectangle2Pt(Component):
    """Create a rectangle from a base plane and two points.

    Inputs:
        plane: Rectangle base plane (Grasshopper Plane [item]).
        point_a: First corner point. (Grasshopper Point A [item]).
        point_b: Second corner point. (Grasshopper Point B [item]).
        radius: Rectangle corner fillet radius (Grasshopper Radius [item]).

    Outputs:
        rectangle: Rectangle defined by P, A and B (Grasshopper Rectangle).
        length: Length of rectangle curve (Grasshopper Length).

    Notes:
        Grasshopper: Curve > Primitive > Rectangle 2Pt (Rec 2Pt).
        pyhopper decisions: the corners are the two points projected onto the plane; a positive radius (clamped to
        half the shorter side) yields Grasshopper's exact rational degree-2 fillet curve, starting on
        the bottom edge and running counter-clockwise; Grasshopper defaults A = origin, B = (10, 5, 0).
    """

    display_name = "Rectangle 2Pt"
    nickname = "Rec 2Pt"
    gh_guid = "575660b1-8c79-4b8d-9222-7ab4a6ddb359"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("point_a", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("point_b", AtomicPoint, Access.ITEM, default=AtomicPoint(10.0, 5.0, 0.0)),
        InputParam("radius", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("rectangle", GEOMETRY),
        OutputParam("length", float),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), point_a=AtomicPoint.origin(), point_b=AtomicPoint(10.0, 5.0, 0.0), radius=0.0):
        centred, width, height = rectangle_from_corners(plane, point_a, point_b)
        return make_rectangle(centred, width, height, radius)
