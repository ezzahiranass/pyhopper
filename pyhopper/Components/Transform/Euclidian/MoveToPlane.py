"""MoveToPlane - Translate (move) an object onto a plane (Grasshopper "Move To Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Bounds import minimum_signed_distance
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Utils.Vectors import scale
from pyhopper.Core.TypeSystem import GEOMETRY


class MoveToPlane(Component):
    """Translate (move) an object onto a plane.

    Inputs:
        geometry: Base geometry (Grasshopper Geometry [item]).
        plane: Target plane (Grasshopper Plane [item]).
        above: Move when above plane (Grasshopper Above [item]).
        below: Move when below plane (Grasshopper Below [item]).

    Outputs:
        geometry: Translated geometry (Grasshopper Geometry).
        transform: Transformation data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Euclidean > Move To Plane (MoveToPlane).
        pyhopper decisions: translates along the plane normal so the geometry's lowest point lands on the plane;
        ``above`` allows geometry entirely above the plane to move down, ``below`` allows geometry
        touching or dipping below the plane to move up (Grasshopper defaults both True); otherwise
        the geometry is untouched and the transform is the identity. Extents follow Bounding Box.
    """

    display_name = "Move To Plane"
    nickname = "MoveToPlane"
    gh_guid = "4fe87ef8-49e4-4605-9859-87940d62e1de"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("above", bool, Access.ITEM, default=True),
        InputParam("below", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("geometry", GEOMETRY),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, plane=AtomicPlane.world_xy(), above=True, below=True):
        lowest = minimum_signed_distance(geometry, plane)
        moves = (lowest > 0.0 and above) or (lowest < 0.0 and below)
        xform = AtomicTransform.translation(scale(plane.normal, -lowest)) if moves else AtomicTransform.identity()
        return apply_transform(xform, geometry), xform
