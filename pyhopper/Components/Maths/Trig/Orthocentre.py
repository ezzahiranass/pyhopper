"""Orthocentre - Generate the triangle orthocentre from altitudes (Grasshopper "Orthocentre")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._triangles import orthocentre_altitudes


class Orthocentre(Component):
    """Generate the triangle orthocentre from altitudes.

    Inputs:
        point_a: First triangle corner (Grasshopper Point A [item]).
        point_b: Second triangle corner (Grasshopper Point B [item]).
        point_c: Third triangle corner (Grasshopper Point C [item]).

    Outputs:
        orthocentre: Orthocentre point for triangle (Grasshopper Orthocentre).
        altitude_ab: Altitude line connecting edge AB with corner C (Grasshopper Altitude AB).
        altitude_bc: Altitude line connecting edge BC with corner A (Grasshopper Altitude BC).
        altitude_ca: Altitude line connecting edge CA with corner B (Grasshopper Altitude CA).

    Notes:
        Grasshopper: Maths > Trig > Orthocentre (OCentre).
        pyhopper decisions: Grasshopper-verified — each altitude runs from its foot on the
        (infinite) edge line to the opposite corner; collinear or coincident corners raise
        ``ValueError`` (Grasshopper emits nulls). Works for triangles in any plane; the corners are
        required (Grasshopper has no defaults either).
    """

    display_name = "Orthocentre"
    nickname = "OCentre"
    gh_guid = "36dd5551-b6bd-4246-bd2f-1fd91eb2f02d"

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM),
        InputParam("point_b", AtomicPoint, Access.ITEM),
        InputParam("point_c", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("orthocentre", AtomicPoint),
        OutputParam("altitude_ab", AtomicLine),
        OutputParam("altitude_bc", AtomicLine),
        OutputParam("altitude_ca", AtomicLine),
    ]

    def generate(self, point_a, point_b, point_c):
        return orthocentre_altitudes(point_a, point_b, point_c)
