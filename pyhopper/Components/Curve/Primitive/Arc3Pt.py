"""Arc3Pt - Create an arc through three points (Grasshopper "Arc 3Pt")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Arcs import arc_from_three_points
from pyhopper.Core.TypeSystem import GEOMETRY


class Arc3Pt(Component):
    """Create an arc through three points.

    Inputs:
        point_a: Start point of arc (Grasshopper Point A [item]).
        point_b: Point on arc interior (Grasshopper Point B [item]).
        point_c: End point of arc (Grasshopper Point C [item]).

    Outputs:
        arc: Resulting arc (Grasshopper Arc).
        plane: Arc plane (Grasshopper Plane).
        radius: Arc radius (Grasshopper Radius).

    Notes:
        Grasshopper: Curve > Primitive > Arc 3Pt (Arc).
        pyhopper decisions: the plane sits at the centre with X towards A and the normal following A -> B -> C;
        collinear (or coincident) points give the line A-C with an infinite radius, like Grasshopper.
    """

    display_name = "Arc 3Pt"
    nickname = "Arc"
    gh_guid = "9fa1b081-b1c7-4a12-a163-0aa8da9ff6c4"

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM),
        InputParam("point_b", AtomicPoint, Access.ITEM),
        InputParam("point_c", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("arc", GEOMETRY),
        OutputParam("plane", AtomicPlane),
        OutputParam("radius", float),
    ]

    def generate(self, point_a=None, point_b=None, point_c=None):
        return arc_from_three_points(point_a, point_b, point_c)
