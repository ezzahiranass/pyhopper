"""TangentLinesIn - Create internal tangent lines between circles (Grasshopper "Tangent Lines (In)")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicCircle, AtomicLine
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Tangency import internal_tangent_lines


class TangentLinesIn(Component):
    """Create internal tangent lines between circles.

    Inputs:
        circle_a: First base circle (Grasshopper Circle A [item]).
        circle_b: Second base circle (Grasshopper Circle B [item]).

    Outputs:
        tangent_1: Primary interior tangent (Grasshopper Tangent 1).
        tangent_2: Secondary interior tangent (Grasshopper Tangent 2).

    Notes:
        Grasshopper: Curve > Primitive > Tangent Lines (In) (TanIn).
        pyhopper decisions: Grasshopper-verified — the crossing tangents run from circle A to circle
        B, the first leaving A counter-clockwise of the A → B direction; intersecting or touching
        circles raise ``ValueError`` (Grasshopper emits nulls). Coplanar circles are assumed.
    """

    display_name = "Tangent Lines (In)"
    nickname = "TanIn"
    gh_guid = "e0168047-c46a-48c6-8595-2fb3d8574f23"

    inputs = [
        InputParam("circle_a", AtomicCircle, Access.ITEM),
        InputParam("circle_b", AtomicCircle, Access.ITEM),
    ]
    outputs = [
        OutputParam("tangent_1", AtomicLine),
        OutputParam("tangent_2", AtomicLine),
    ]

    def generate(self, circle_a, circle_b):
        return internal_tangent_lines(circle_a, circle_b)
