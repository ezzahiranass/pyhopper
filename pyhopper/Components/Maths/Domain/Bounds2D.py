"""Bounds2D - Create a numeric two-dimensional domain which encompasses a list of coordinates (Grasshopper "Bounds 2D")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicInterval2, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Bounds2D(Component):
    """Create a numeric two-dimensional domain which encompasses a list of coordinates.

    Inputs:
        coordinates: Two dimensional coordinates to include in Bounds (Grasshopper Coordinates [list]).

    Outputs:
        domain: Numeric two-dimensional domain between the lowest and highest numbers in {N.x ; N.y} (Grasshopper Domain).

    Notes:
        Grasshopper: Maths > Domain > Bounds 2D (Bnd).
        pyhopper decisions: Grasshopper-verified — U spans the lowest to highest x coordinate and V the
        lowest to highest y coordinate of the points (z is ignored); an empty list raises ``ValueError``
        (Grasshopper emits nothing).
    """

    display_name = "Bounds 2D"
    nickname = "Bnd"
    gh_guid = "dd53b24c-003a-4a04-b185-a44d91633cbe"

    inputs = [
        InputParam("coordinates", AtomicPoint, Access.LIST),
    ]
    outputs = [
        OutputParam("domain", AtomicInterval2),
    ]

    def generate(self, coordinates=None):
        points = list(coordinates or [])
        if not points:
            raise ValueError("Bounds2D needs at least one point")
        xs, ys = [p.x for p in points], [p.y for p in points]
        return AtomicInterval2(AtomicInterval(min(xs), max(xs)), AtomicInterval(min(ys), max(ys)))
