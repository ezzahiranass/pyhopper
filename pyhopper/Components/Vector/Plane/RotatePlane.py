"""RotatePlane - Perform plane rotation around plane z-axis (Grasshopper "Rotate Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicTransform


class RotatePlane(Component):
    """Perform plane rotation around plane z-axis.

    Inputs:
        plane: Plane to rotate (Grasshopper Plane [item]).
        angle: Rotation (counter clockwise) around plane z-axis in radians (Grasshopper Angle [item]).

    Outputs:
        plane: Rotated plane (Grasshopper Plane).

    Notes:
        Grasshopper: Vector > Plane > Rotate Plane (PRot).
        pyhopper decisions: none; the axes rotate about the normal by ``angle`` radians (counter-clockwise seen from the normal).
    """

    display_name = "Rotate Plane"
    nickname = "PRot"
    gh_guid = "f6f14b09-6497-4564-8403-09e4eb5a6b82"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("angle", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), angle=0.0):
        rotation = AtomicTransform.rotation(plane.origin, plane.normal, float(angle))
        return AtomicPlane(plane.origin, plane.normal, rotation.transform_vector(plane.x_axis))
