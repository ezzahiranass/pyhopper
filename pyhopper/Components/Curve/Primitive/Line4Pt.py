"""Line4Pt - Create a line from four points (Grasshopper "Line 4Pt")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Vectors import dot, sub, translate, unit, vector_between


class Line4Pt(Component):
    """Create a line from four points.

    Inputs:
        line: Guide line. (Grasshopper Line [item]).
        point_a: First point to project onto the guide. (Grasshopper Point A [item]).
        point_b: Second point to project onto the guide. (Grasshopper Point B [item]).

    Outputs:
        line: Line segment between A and B (Grasshopper Line).

    Notes:
        Grasshopper: Curve > Primitive > Line 4Pt (Ln4Pt).
        pyhopper decisions: none; the line from the projection of A onto the guide's infinite line to the projection of B.
    """

    display_name = "Line 4Pt"
    nickname = "Ln4Pt"
    gh_guid = "b9fde5fa-d654-4306-8ee1-6b69e6757604"

    inputs = [
        InputParam("line", AtomicLine, Access.ITEM),
        InputParam("point_a", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("point_b", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
    ]
    outputs = [
        OutputParam("line", AtomicLine),
    ]

    def generate(self, line=None, point_a=AtomicPoint.origin(), point_b=AtomicPoint.origin()):
        direction = unit(vector_between(line.start, line.end))
        projected = [translate(line.start, direction, dot(sub(point, line.start), direction)) for point in (point_a, point_b)]
        return AtomicLine(projected[0], projected[1])
