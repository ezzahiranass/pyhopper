"""Arc - Create an arc defined by base plane, radius and angle domain (Grasshopper "Arc")."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicArc, AtomicInterval, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Arcs import arc_from_plane, arc_length


class Arc(Component):
    """Create an arc defined by base plane, radius and angle domain.

    Inputs:
        plane: Base plane of arc (Grasshopper Plane [item]).
        radius: Radius of arc (Grasshopper Radius [item]).
        angle: Angle domain in radians (Grasshopper Angle [item]).

    Outputs:
        arc: Resulting arc (Grasshopper Arc).
        length: Arc length (Grasshopper Length).

    Notes:
        Grasshopper: Curve > Primitive > Arc (Arc).
        pyhopper decisions: angles in radians; a descending angle domain flips the plane normal and negates the
        angles, exactly as Grasshopper normalises it; Grasshopper defaults ``radius = 1``,
        ``angle = [0, pi]``.
    """

    display_name = "Arc"
    nickname = "Arc"
    gh_guid = "bb59bffc-f54c-4682-9778-f6c3fe74fce3"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("radius", float, Access.ITEM, default=1.0),
        InputParam("angle", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, math.pi)),
    ]
    outputs = [
        OutputParam("arc", AtomicArc),
        OutputParam("length", float),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), radius=1.0, angle=AtomicInterval(0.0, math.pi)):
        arc = arc_from_plane(plane, radius, angle)
        return arc, arc_length(arc)
