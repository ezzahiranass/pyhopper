"""Centroid - Generate the triangle centroid from medians (Grasshopper "Centroid")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._triangles import centroid_medians


class Centroid(Component):
    """Generate the triangle centroid from medians.

    Inputs:
        point_a: First triangle corner (Grasshopper Point A [item]).
        point_b: Second triangle corner (Grasshopper Point B [item]).
        point_c: Third triangle corner (Grasshopper Point C [item]).

    Outputs:
        centroid: Centroid point for triangle (Grasshopper Centroid).
        median_ab: Median line connecting edge AB with corner C (Grasshopper Median AB).
        median_bc: Median line connecting edge BC with corner A (Grasshopper Median BC).
        median_ca: Median line connecting edge CA with corner B (Grasshopper Median CA).

    Notes:
        Grasshopper: Maths > Trig > Centroid (Centroid).
        pyhopper decisions: Grasshopper-verified — each median runs from the edge midpoint to the
        opposite corner; collinear or coincident corners raise
        ``ValueError`` (Grasshopper emits nulls). Works for triangles in any plane; the corners are
        required (Grasshopper has no defaults either).
    """

    display_name = "Centroid"
    nickname = "Centroid"
    gh_guid = "afbcbad4-2a2a-4954-8040-d999e316d2bd"

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM),
        InputParam("point_b", AtomicPoint, Access.ITEM),
        InputParam("point_c", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("centroid", AtomicPoint),
        OutputParam("median_ab", AtomicLine),
        OutputParam("median_bc", AtomicLine),
        OutputParam("median_ca", AtomicLine),
    ]

    def generate(self, point_a, point_b, point_c):
        return centroid_medians(point_a, point_b, point_c)
