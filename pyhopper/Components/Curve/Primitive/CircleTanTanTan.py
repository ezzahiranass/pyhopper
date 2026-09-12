"""CircleTanTanTan - Create a circle tangent to three curves (Grasshopper "Circle TanTanTan")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicCircle, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Tangency import tangent_circle_three
from pyhopper.Core.TypeSystem import CURVE


class CircleTanTanTan(Component):
    """Create a circle tangent to three curves.

    Inputs:
        curve_a: First curve for tangency constraint (Grasshopper Curve A [item]).
        curve_b: Second curve for tangency constraint (Grasshopper Curve B [item]).
        curve_c: Third curve for tangency constraint (Grasshopper Curve C [item]).
        point: Circle center point guide (Grasshopper Point [item]).

    Outputs:
        circle: Resulting circle (Grasshopper Circle).

    Notes:
        Grasshopper: Curve > Primitive > Circle TanTanTan (CircleTTT).
        pyhopper decisions: the Apollonius circle tangent to all three curves whose centre is closest
        to the guide point (Grasshopper-verified for guide points inside the gap; Grasshopper's
        iterative fit fails for guide points near the outer solutions, which pyhopper still returns);
        lines, circles and arcs are supported (general curves need the K3 closest-point kernel); no solution raises ``ValueError``.
    """

    display_name = "Circle TanTanTan"
    nickname = "CircleTTT"
    gh_guid = "dcaa922d-5491-4826-9a22-5adefa139f43"

    inputs = [
        InputParam("curve_a", CURVE, Access.ITEM),
        InputParam("curve_b", CURVE, Access.ITEM),
        InputParam("curve_c", CURVE, Access.ITEM),
        InputParam("point", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("circle", AtomicCircle),
    ]

    def generate(self, curve_a, curve_b, curve_c, point):
        return tangent_circle_three([curve_a, curve_b, curve_c], point)
