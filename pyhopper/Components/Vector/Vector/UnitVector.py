"""UnitVector - Unitize vector (Grasshopper "Unit Vector")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Vectors import unit


class UnitVector(Component):
    """Unitize vector.

    Inputs:
        vector: Base vector (Grasshopper Vector [item]).

    Outputs:
        vector: Unit vector (Grasshopper Vector).

    Notes:
        Grasshopper: Vector > Vector > Unit Vector (Unit).
        pyhopper decisions: none; a zero vector stays zero, as in Grasshopper.
    """

    display_name = "Unit Vector"
    nickname = "Unit"
    gh_guid = "d2da1306-259a-4994-85a4-672d8a4c7805"

    inputs = [
        InputParam("vector", AtomicVector, Access.ITEM, default=AtomicVector.unit_x()),
    ]
    outputs = [
        OutputParam("vector", AtomicVector),
    ]

    def generate(self, vector=AtomicVector.unit_x()):
        return unit(vector)
