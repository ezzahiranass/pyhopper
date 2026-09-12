"""OrientDirection - Orient an object using directional constraints only (Grasshopper "Orient Direction")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicTransform, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Utils.Vectors import length, sub
from pyhopper.Core.TypeSystem import GEOMETRY


class OrientDirection(Component):
    """Orient an object using directional constraints only.

    Inputs:
        geometry: Base geometry (Grasshopper Geometry [item]).
        point_a: Reference point (Grasshopper Point A [item]).
        direction_a: Reference direction (Grasshopper Direction A [item]).
        point_b: Target point (Grasshopper Point B [item]).
        direction_b: Target direction (Grasshopper Direction B [item]).

    Outputs:
        geometry: Reoriented geometry (Grasshopper Geometry).
        transform: Transformation data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Affine > Orient Direction (Orient).
        pyhopper decisions: Grasshopper-verified — the translation from A to B, the minimal rotation
        about B taking direction A onto direction B, then a uniform scale about B by |direction B| /
        |direction A| (Grasshopper does not normalise the directions); zero directions raise
        ``ValueError``. Without geometry only the transform is emitted.
    """

    display_name = "Orient Direction"
    nickname = "Orient"
    gh_guid = "1602b2cc-007c-4b79-8926-0067c6184e44"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM, optional=True),
        InputParam("point_a", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("direction_a", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
        InputParam("point_b", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("direction_b", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
    ]
    outputs = [
        OutputParam("geometry", GEOMETRY),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, point_a=AtomicPoint.origin(), direction_a=AtomicVector.unit_z(), point_b=AtomicPoint.origin(), direction_b=AtomicVector.unit_z()):
        xform = AtomicTransform.compound([
            AtomicTransform.translation(sub(point_b, point_a)),
            AtomicTransform.rotation_to_direction(point_b, direction_a, direction_b),
            AtomicTransform.scale(point_b, length(direction_b) / length(direction_a)),
        ])
        return (Component.NO_OUTPUT if geometry is None else apply_transform(xform, geometry)), xform
