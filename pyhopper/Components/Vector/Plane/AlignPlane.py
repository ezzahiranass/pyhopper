"""AlignPlane - Perform minimal rotation to align a plane with a guide vector (Grasshopper "Align Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Planes import align_plane


class AlignPlane(Component):
    """Perform minimal rotation to align a plane with a guide vector.

    Inputs:
        plane: Plane to straighten (Grasshopper Plane [item]).
        direction: Straightening guide direction (Grasshopper Direction [item]).

    Outputs:
        plane: Straightened plane (Grasshopper Plane).
        angle: Rotation angle (Grasshopper Angle).

    Notes:
        Grasshopper: Vector > Plane > Align Plane (Align).
        pyhopper decisions: rotates about the plane normal so the x axis follows the direction projected onto the
        plane; ``angle`` is the signed rotation in radians. A direction parallel to the normal
        raises ``ValueError`` (Grasshopper silently falls back to the y axis).
    """

    display_name = "Align Plane"
    nickname = "Align"
    gh_guid = "e76040ec-3b91-41e1-8e00-c74c23b89391"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("direction", AtomicVector, Access.ITEM),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
        OutputParam("angle", float),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), direction=None):
        return align_plane(plane, direction)
