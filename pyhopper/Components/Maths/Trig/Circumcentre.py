"""Circumcentre - Generate the triangle circumcentre from perpendicular bisectors (Grasshopper "Circumcentre")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._triangles import circumcentre_bisectors


class Circumcentre(Component):
    """Generate the triangle circumcentre from perpendicular bisectors.

    Inputs:
        point_a: First triangle corner (Grasshopper Point A [item]).
        point_b: Second triangle corner (Grasshopper Point B [item]).
        point_c: Third triangle corner (Grasshopper Point C [item]).

    Outputs:
        circumcentre: Circumcentre point for triangle (Grasshopper Circumcentre).
        bisector_ab: Perpendicular bisector line emanating from edge AB (Grasshopper Bisector AB).
        bisector_bc: Perpendicular bisector line emanating from edge AB (Grasshopper Bisector BC).
        bisector_ca: Perpendicular bisector line emanating from edge AB (Grasshopper Bisector CA).

    Notes:
        Grasshopper: Maths > Trig > Circumcentre (CCentre).
        pyhopper decisions: Grasshopper-verified — each bisector runs from the edge midpoint,
        perpendicular to the edge into the triangle, up to the first other edge it meets (not to the
        circumcentre, which lies outside obtuse triangles); collinear or coincident corners raise
        ``ValueError`` (Grasshopper emits nulls). Works for triangles in any plane; the corners are
        required (Grasshopper has no defaults either).
    """

    display_name = "Circumcentre"
    nickname = "CCentre"
    gh_guid = "21d0767c-5340-4087-aa09-398d0e706908"

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM),
        InputParam("point_b", AtomicPoint, Access.ITEM),
        InputParam("point_c", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("circumcentre", AtomicPoint),
        OutputParam("bisector_ab", AtomicLine),
        OutputParam("bisector_bc", AtomicLine),
        OutputParam("bisector_ca", AtomicLine),
    ]

    def generate(self, point_a, point_b, point_c):
        return circumcentre_bisectors(point_a, point_b, point_c)
