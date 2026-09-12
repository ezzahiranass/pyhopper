"""TangentLines - Create tangent lines between a point and a circle (Grasshopper "Tangent Lines")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicCircle, AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Tangency import tangent_lines_point_circle


class TangentLines(Component):
    """Create tangent lines between a point and a circle.

    Inputs:
        point: Point for tangent lines (Grasshopper Point [item]).
        circle: Base circle (Grasshopper Circle [item]).

    Outputs:
        tangent_1: Primary tangent (Grasshopper Tangent 1).
        tangent_2: Secondary tangent (Grasshopper Tangent 2).

    Notes:
        Grasshopper: Curve > Primitive > Tangent Lines (Tan).
        pyhopper decisions: Grasshopper-verified — both lines run from the point to the circle; the
        first touches the circle counter-clockwise of the centre → point direction, the second
        clockwise; a point on or inside the circle raises ``ValueError`` (Grasshopper emits nulls).
        The point is required (Grasshopper has no default).
    """

    display_name = "Tangent Lines"
    nickname = "Tan"
    gh_guid = "ea0f0996-af7a-481d-8099-09c041e6c2d5"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM),
        InputParam("circle", AtomicCircle, Access.ITEM),
    ]
    outputs = [
        OutputParam("tangent_1", AtomicLine),
        OutputParam("tangent_2", AtomicLine),
    ]

    def generate(self, point, circle):
        return tangent_lines_point_circle(point, circle)
