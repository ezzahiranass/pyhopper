"""InCircle - Create the incircle of a triangle (Grasshopper "InCircle")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicCircle, AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveFitting import incircle


class InCircle(Component):
    """Create the incircle of a triangle.

    Inputs:
        corner_a: First corner of triangle (Grasshopper Corner A [item]).
        corner_b: Second corner of triangle (Grasshopper Corner B [item]).
        corner_c: Third corner of triangle (Grasshopper Corner C [item]).

    Outputs:
        circle: Resulting circle (Grasshopper Circle).
        plane: Circle plane (Grasshopper Plane).
        radius: Circle radius (Grasshopper Radius).

    Notes:
        Grasshopper: Curve > Primitive > InCircle (InCircle).
        pyhopper decisions: none; the plane sits on the incentre with the triangle normal ``AB × AC``
        and x along AB, as Grasshopper reports; a degenerate triangle raises ``ValueError``.
    """

    display_name = "InCircle"
    nickname = "InCircle"
    gh_guid = "28b1c4d4-ab1c-4309-accd-1b7a954ed948"

    inputs = [
        InputParam("corner_a", AtomicPoint, Access.ITEM),
        InputParam("corner_b", AtomicPoint, Access.ITEM),
        InputParam("corner_c", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("circle", AtomicCircle),
        OutputParam("plane", AtomicPlane),
        OutputParam("radius", float),
    ]

    def generate(self, corner_a=None, corner_b=None, corner_c=None):
        return incircle(corner_a, corner_b, corner_c)
