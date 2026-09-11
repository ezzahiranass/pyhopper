"""BoundingBox - Solve oriented geometry bounding boxes (Grasshopper "Bounding Box")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBox, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Bounds import bounding_boxes
from pyhopper.Core.TypeSystem import GEOMETRY


class BoundingBox(Component):
    """Solve oriented geometry bounding boxes.

    Inputs:
        content: Geometry to contain (Grasshopper Content [list]).
        plane: BoundingBox orientation plane (Grasshopper Plane [item]).

    Outputs:
        box: Aligned bounding box in world coordinates (Grasshopper Box).
        plane_box: Bounding box in orientation plane coordinates (Grasshopper Box).

    Notes:
        Grasshopper: Surface > Primitive > Bounding Box (BBox).
        pyhopper decisions: one box per content item (set ``union`` for a single box around everything, Grasshopper's
        "Union Box" menu option); ``box`` is aligned to the plane in world space, ``plane_box`` holds the
        same extents in plane coordinates (Grasshopper's second output). Points, lines, polylines,
        rectangles, boxes, meshes, circles and arcs are exact; NURBS curves and surfaces use their
        control nets, so those boxes can be larger than Grasshopper's tight ones.
    """

    display_name = "Bounding Box"
    nickname = "BBox"
    gh_guid = "0bb3d234-9097-45db-9998-621639c87d3b"
    gh_extra_inputs = ("union",)

    inputs = [
        InputParam("content", GEOMETRY, Access.LIST),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("union", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("box", AtomicBox, access=Access.LIST),
        OutputParam("plane_box", AtomicBox, access=Access.LIST),
    ]

    def generate(self, content=None, plane=AtomicPlane.world_xy(), union=False):
        return bounding_boxes(list(content or []), plane, bool(union))
