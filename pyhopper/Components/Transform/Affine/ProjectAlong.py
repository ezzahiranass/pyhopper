"""ProjectAlong - Project an object onto a plane along a direction (Grasshopper "Project Along")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Utils.Vectors import dot, length


class ProjectAlong(Component):
    """Project an object onto a plane along a direction.

    Inputs:
        geometry: Geometry to project (Grasshopper Geometry [item]).
        plane: Projection plane (Grasshopper Plane [item]).
        direction: Projection direction (Grasshopper Direction [item]).

    Outputs:
        geometry: Projected geometry (Grasshopper Geometry).
        transform: Transformation data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Affine > Project Along (ProjectA).
        pyhopper decisions: an oblique projection onto the plane along ``direction`` (default -Z as in
        Grasshopper); a direction parallel to the plane raises ``ValueError`` where Grasshopper emits
        null. Without geometry only the transform is emitted.
    """

    display_name = "Project Along"
    nickname = "ProjectA"
    gh_guid = "06d7bc4a-ba3e-4445-8ab5-079613b52f28"

    inputs = [
        InputParam("geometry", None, Access.ITEM, optional=True),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("direction", AtomicVector, Access.ITEM, default=AtomicVector(0.0, 0.0, -1.0)),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, plane=AtomicPlane.world_xy(), direction=AtomicVector(0.0, 0.0, -1.0)):
        if abs(dot(direction, plane.normal)) <= 1e-12 * max(1.0, length(direction)):
            raise ValueError("ProjectAlong needs a direction that is not parallel to the plane")
        xform = AtomicTransform.projection(plane, direction)
        return (Component.NO_OUTPUT if geometry is None else apply_transform(xform, geometry)), xform
