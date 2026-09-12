"""PlaneNormal - Create a plane perpendicular to a vector (Grasshopper "Plane Normal")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Planes import plane_from_normal


class PlaneNormal(Component):
    """Create a plane perpendicular to a vector.

    Inputs:
        origin: Origin of plane (Grasshopper Origin [item]).
        z_axis: Z-Axis direction of plane (Grasshopper Z-Axis [item]).

    Outputs:
        plane: Plane definition (Grasshopper Plane).

    Notes:
        Grasshopper: Vector > Plane > Plane Normal (Pl).
        pyhopper decisions: the x axis is Rhino's choice for a plane built from a normal (``Vectors.perpendicular``,
        a port of openNURBS ``PerpendicularTo``); a zero normal raises ``ValueError``.
    """

    display_name = "Plane Normal"
    nickname = "Pl"
    gh_guid = "cfb6b17f-ca82-4f5d-b604-d4f69f569de3"

    inputs = [
        InputParam("origin", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("z_axis", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
    ]

    def generate(self, origin=AtomicPoint.origin(), z_axis=AtomicVector.unit_z()):
        return plane_from_normal(origin, z_axis)
