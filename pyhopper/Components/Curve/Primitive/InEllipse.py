"""InEllipse - Create the inscribed ellipse (Steiner ellipse) of a triangle (Grasshopper "InEllipse")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Tangency import steiner_inellipse
from pyhopper.Core.TypeSystem import CURVE


class InEllipse(Component):
    """Create the inscribed ellipse (Steiner ellipse) of a triangle.

    Inputs:
        corner_a: First corner of triangle (Grasshopper Corner A [item]).
        corner_b: Second corner of triangle (Grasshopper Corner B [item]).
        corner_c: Third corner of triangle (Grasshopper Corner C [item]).

    Outputs:
        ellipse: Resulting ellipse (Grasshopper Ellipse).
        plane: Ellipse plane (Grasshopper Plane).

    Notes:
        Grasshopper: Curve > Primitive > InEllipse (InEllipse).
        pyhopper decisions: Grasshopper-verified — the ellipse is the incircle of the unit equilateral
        triangle mapped affinely onto ABC, emitted as Rhino's rational quadratic NURBS (nine control
        points, knots in the incircle's arc length); the plane has its origin at A and its x axis
        towards B. Collinear corners raise ``ValueError``; the corners are required.
    """

    display_name = "InEllipse"
    nickname = "InEllipse"
    gh_guid = "679a9c6a-ab97-4c20-b02c-680f9a9a1a44"

    inputs = [
        InputParam("corner_a", AtomicPoint, Access.ITEM),
        InputParam("corner_b", AtomicPoint, Access.ITEM),
        InputParam("corner_c", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("ellipse", CURVE),
        OutputParam("plane", AtomicPlane),
    ]

    def generate(self, corner_a, corner_b, corner_c):
        return steiner_inellipse(corner_a, corner_b, corner_c)
