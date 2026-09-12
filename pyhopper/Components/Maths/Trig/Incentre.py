"""Incentre - Generate the triangle incentre from angle bisectors (Grasshopper "Incentre")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._triangles import incentre_bisectors


class Incentre(Component):
    """Generate the triangle incentre from angle bisectors.

    Inputs:
        point_a: First triangle corner (Grasshopper Point A [item]).
        point_b: Second triangle corner (Grasshopper Point B [item]).
        point_c: Third triangle corner (Grasshopper Point C [item]).

    Outputs:
        incentre: Incentre point for triangle (Grasshopper Incentre).
        bisector_a: Perpendicular bisector line emanating from corner A (Grasshopper Bisector A).
        bisector_b: Perpendicular bisector line emanating from corner B (Grasshopper Bisector B).
        bisector_c: Perpendicular bisector line emanating from corner C (Grasshopper Bisector C).

    Notes:
        Grasshopper: Maths > Trig > Incentre (ICentre).
        pyhopper decisions: Grasshopper-verified — each angle bisector runs from its corner to the
        opposite edge (meeting it in the ratio of the adjacent sides); collinear or coincident corners raise
        ``ValueError`` (Grasshopper emits nulls). Works for triangles in any plane; the corners are
        required (Grasshopper has no defaults either).
    """

    display_name = "Incentre"
    nickname = "ICentre"
    gh_guid = "c3342ea2-e181-46aa-a9b9-e438ccbfb831"

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM),
        InputParam("point_b", AtomicPoint, Access.ITEM),
        InputParam("point_c", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("incentre", AtomicPoint),
        OutputParam("bisector_a", AtomicLine),
        OutputParam("bisector_b", AtomicLine),
        OutputParam("bisector_c", AtomicLine),
    ]

    def generate(self, point_a, point_b, point_c):
        return incentre_bisectors(point_a, point_b, point_c)
