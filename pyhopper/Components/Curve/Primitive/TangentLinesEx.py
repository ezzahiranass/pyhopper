"""TangentLinesEx - Create external tangent lines between circles (Grasshopper "Tangent Lines (Ex)")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicCircle, AtomicLine
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Tangency import external_tangent_lines


class TangentLinesEx(Component):
    """Create external tangent lines between circles.

    Inputs:
        circle_a: First base circle (Grasshopper Circle A [item]).
        circle_b: Second base circle (Grasshopper Circle B [item]).

    Outputs:
        tangent_1: Primary exterior tangent (Grasshopper Tangent 1).
        tangent_2: Secondary exterior tangent (Grasshopper Tangent 2).

    Notes:
        Grasshopper: Curve > Primitive > Tangent Lines (Ex) (TanEx).
        pyhopper decisions: Grasshopper-verified — the tangents run from circle A to circle B, the
        first touching A counter-clockwise of the A → B direction; when one circle contains the
        other ``ValueError`` is raised (Grasshopper emits nulls). Coplanar circles are assumed.
    """

    display_name = "Tangent Lines (Ex)"
    nickname = "TanEx"
    gh_guid = "d6d68c93-d00f-4cd5-ba89-903c7f6be64c"

    inputs = [
        InputParam("circle_a", AtomicCircle, Access.ITEM),
        InputParam("circle_b", AtomicCircle, Access.ITEM),
    ]
    outputs = [
        OutputParam("tangent_1", AtomicLine),
        OutputParam("tangent_2", AtomicLine),
    ]

    def generate(self, circle_a, circle_b):
        return external_tangent_lines(circle_a, circle_b)
