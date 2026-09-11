"""Box2Pt - Create a box defined by two points (Grasshopper "Box 2Pt")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBox, AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Boxes import box_from_corners


class Box2Pt(Component):
    """Create a box defined by two points.

    Inputs:
        point_a: First corner (Grasshopper Point A [item]).
        point_b: Second corner (Grasshopper Point B [item]).
        plane: Base plane (Grasshopper Plane [item]).

    Outputs:
        box: Resulting box (Grasshopper Box).

    Notes:
        Grasshopper: Surface > Primitive > Box 2Pt (Box).
        pyhopper decisions: the corners are the two points in the plane's coordinates; the box is centred on its plane
        (pyhopper's box representation) with the same corners Grasshopper produces.
    """

    display_name = "Box 2Pt"
    nickname = "Box"
    gh_guid = "2a43ef96-8f87-4892-8b94-237a47e8d3cf"

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM),
        InputParam("point_b", AtomicPoint, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("box", AtomicBox),
    ]

    def generate(self, point_a=None, point_b=None, plane=AtomicPlane.world_xy()):
        return box_from_corners(plane, point_a, point_b)
