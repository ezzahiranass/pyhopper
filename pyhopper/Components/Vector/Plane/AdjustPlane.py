"""AdjustPlane - Adjust a plane to match a new normal direction (Grasshopper "Adjust Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Utils.Vectors import length


class AdjustPlane(Component):
    """Adjust a plane to match a new normal direction.

    Inputs:
        plane: Plane to adjust (Grasshopper Plane [item]).
        normal: New plane z-axis direction (Grasshopper Normal [item]).

    Outputs:
        plane: Adjusted plane (Grasshopper Plane).

    Notes:
        Grasshopper: Vector > Plane > Adjust Plane (PAdjust).
        pyhopper decisions: the minimal rotation about the origin taking the plane's normal onto the
        new normal, applied to the plane (Grasshopper-verified: an opposite normal turns the plane
        about its x axis); a zero normal raises ``ValueError``.
    """

    display_name = "Adjust Plane"
    nickname = "PAdjust"
    gh_guid = "9ce34996-d8c6-40d3-b442-1a7c8c093614"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("normal", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), normal=AtomicVector.unit_z()):
        if length(normal) <= 1e-12:
            raise ValueError("AdjustPlane needs a non-zero normal")
        return apply_transform(AtomicTransform.rotation_to_direction(plane.origin, plane.normal, normal), plane)
