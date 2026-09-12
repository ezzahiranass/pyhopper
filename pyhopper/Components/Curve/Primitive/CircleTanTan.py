"""CircleTanTan - Create a circle tangent to two curves (Grasshopper "Circle TanTan")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicCircle, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Tangency import tangent_circle_two
from pyhopper.Core.TypeSystem import CURVE


class CircleTanTan(Component):
    """Create a circle tangent to two curves.

    Inputs:
        curve_a: First curve for tangency constraint (Grasshopper Curve A [item]).
        curve_b: Second curve for tangency constraint (Grasshopper Curve B [item]).
        point: Circle center point guide (Grasshopper Point [item]).

    Outputs:
        circle: Resulting circle (Grasshopper Circle).

    Notes:
        Grasshopper: Curve > Primitive > Circle TanTan (CircleTT).
        pyhopper decisions: Grasshopper-verified — the circle touches curve B at B's point closest to
        the guide point and is tangent to curve A, on the guide point's side of B (external tangency
        to a circle A is preferred); lines, circles and arcs are supported (general curves need the K3 closest-point kernel); no solution raises ``ValueError``.
    """

    display_name = "Circle TanTan"
    nickname = "CircleTT"
    gh_guid = "50b204ef-d3de-41bb-a006-02fba2d3f709"

    inputs = [
        InputParam("curve_a", CURVE, Access.ITEM),
        InputParam("curve_b", CURVE, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("circle", AtomicCircle),
    ]

    def generate(self, curve_a, curve_b, point):
        return tangent_circle_two(curve_a, curve_b, point)
