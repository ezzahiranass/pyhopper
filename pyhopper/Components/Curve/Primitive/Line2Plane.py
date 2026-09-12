"""Line2Plane - Create a line between two planes (Grasshopper "Line 2Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Vectors import dot, sub, translate, vector_between


class Line2Plane(Component):
    """Create a line between two planes.

    Inputs:
        line: Guide line. (Grasshopper Line [item]).
        plane_a: First plane to intersect with the guide. (Grasshopper Plane A [item]).
        plane_b: Second plane to intersect with the guide. (Grasshopper Plane B [item]).

    Outputs:
        line: Line segment between A and B (Grasshopper Line).

    Notes:
        Grasshopper: Curve > Primitive > Line 2Plane (Ln2Pl).
        pyhopper decisions: the infinite line through the guide, from its intersection with plane A to
        the one with plane B (Grasshopper-verified); a guide parallel to either plane raises
        ``ValueError`` (Grasshopper emits null).
    """

    display_name = "Line 2Plane"
    nickname = "Ln2Pl"
    gh_guid = "510c4a63-b9bf-42e7-9d07-9d71290264da"

    inputs = [
        InputParam("line", AtomicLine, Access.ITEM),
        InputParam("plane_a", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("plane_b", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("line", AtomicLine),
    ]

    def generate(self, line=None, plane_a=AtomicPlane.world_xy(), plane_b=AtomicPlane.world_xy()):
        direction = vector_between(line.start, line.end)
        hits = []
        for name, plane in (("A", plane_a), ("B", plane_b)):
            slope = dot(direction, plane.normal)
            if abs(slope) < 1e-12:
                raise ValueError(f"Line2Plane guide does not intersect plane {name}")
            t = dot(sub(plane.origin, line.start), plane.normal) / slope
            hits.append(translate(line.start, direction, t))
        return AtomicLine(hits[0], hits[1])
