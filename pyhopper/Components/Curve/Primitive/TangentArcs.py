"""TangentArcs - Create tangent arcs between circles (Grasshopper "Tangent Arcs")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicArc, AtomicCircle
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Tangency import tangent_arcs


class TangentArcs(Component):
    """Create tangent arcs between circles.

    Inputs:
        circle_a: First base circle (Grasshopper Circle A [item]).
        circle_b: Second base circle (Grasshopper Circle B [item]).
        radius: Radius of tangent arcs (Grasshopper Radius [item]).

    Outputs:
        arc_a: First tangent arc solution (Grasshopper Arc A).
        arc_b: Second tangent arc solution (Grasshopper Arc B).

    Notes:
        Grasshopper: Curve > Primitive > Tangent Arcs (TArc).
        pyhopper decisions: Grasshopper-verified — the two fillet arcs of the given radius externally
        tangent to both circles, each running from its tangent point on A to its tangent point on B
        through the gap between the circles; arc A has its centre on the right of the A → B direction.
        A radius too small to bridge the gap (or overlapping circles) raises ``ValueError``. Default
        radius 1 (Grasshopper has none).
    """

    display_name = "Tangent Arcs"
    nickname = "TArc"
    gh_guid = "f1c0783b-60e9-42a7-8081-925bc755494c"

    inputs = [
        InputParam("circle_a", AtomicCircle, Access.ITEM),
        InputParam("circle_b", AtomicCircle, Access.ITEM),
        InputParam("radius", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("arc_a", AtomicArc),
        OutputParam("arc_b", AtomicArc),
    ]

    def generate(self, circle_a, circle_b, radius=1.0):
        return tangent_arcs(circle_a, circle_b, float(radius))
