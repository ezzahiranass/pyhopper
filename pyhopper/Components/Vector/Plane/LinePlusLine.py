"""LinePlusLine - Create a plane from two line segments (Grasshopper "Line + Line")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Vectors import cross, is_zero, vector_between


class LinePlusLine(Component):
    """Create a plane from two line segments.

    Inputs:
        line_a: First line constraint. Plane origin will be at line start. (Grasshopper Line A [item]).
        line_b: Second line constraint. Line B should be co-planar with but not parallel to Line A. (Grasshopper Line B [item]).

    Outputs:
        plane: Plane definition (Grasshopper Plane).

    Notes:
        Grasshopper: Vector > Plane > Line + Line (LnLn).
        pyhopper decisions: origin at the start of line A, x axis along A, normal ``A × B``;
        parallel or collinear lines leave the orientation undefined and raise ``ValueError``
        (Grasshopper emits null).
    """

    display_name = "Line + Line"
    nickname = "LnLn"
    gh_guid = "d788ad7f-6d68-4106-8b2f-9e55e6e107c0"

    inputs = [
        InputParam("line_a", AtomicLine, Access.ITEM),
        InputParam("line_b", AtomicLine, Access.ITEM),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
    ]

    def generate(self, line_a=None, line_b=None):
        direction_a = vector_between(line_a.start, line_a.end)
        direction_b = vector_between(line_b.start, line_b.end)
        normal = cross(direction_a, direction_b)
        if is_zero(normal):
            raise ValueError("LinePlusLine needs lines that are not parallel")
        return AtomicPlane(line_a.start, normal, direction_a)
