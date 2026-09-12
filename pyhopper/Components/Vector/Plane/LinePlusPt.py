"""LinePlusPt - Create a plane from a line and a point (Grasshopper "Line + Pt")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Vectors import cross, is_zero, vector_between


class LinePlusPt(Component):
    """Create a plane from a line and a point.

    Inputs:
        line: Line constraint. Plane origin will be at line startpoint. Plane x-axis will be parallel to line direction. (Grasshopper Line [item]).
        point: Point on plane. Point must not be co-linear with line. (Grasshopper Point [item]).

    Outputs:
        plane: Plane definition (Grasshopper Plane).

    Notes:
        Grasshopper: Vector > Plane > Line + Pt (LnPt).
        pyhopper decisions: origin at the line start, x axis along the line, the point on the
        positive y side; a point on the line raises ``ValueError`` (Grasshopper emits null).
    """

    display_name = "Line + Pt"
    nickname = "LnPt"
    gh_guid = "ccc3f2ff-c9f6-45f8-aa30-8a924a9bda36"

    inputs = [
        InputParam("line", AtomicLine, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
    ]

    def generate(self, line=None, point=AtomicPoint.origin()):
        direction = vector_between(line.start, line.end)
        normal = cross(direction, vector_between(line.start, point))
        if is_zero(normal):
            raise ValueError("LinePlusPt needs a point off the line")
        return AtomicPlane(line.start, normal, direction)
