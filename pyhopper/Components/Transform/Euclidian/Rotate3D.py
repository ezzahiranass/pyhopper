"""Rotate3D - Rotate an object around a center point and an axis vector (Grasshopper "Rotate 3D")."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicPoint, AtomicTransform, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Core.TypeSystem import GEOMETRY


class Rotate3D(Component):
    """Rotate an object around a center point and an axis vector.

    Inputs:
        geometry: Base geometry (Grasshopper Geometry [item]).
        angle: Rotation angle in radians (Grasshopper Angle [item]).
        center: Center of rotation (Grasshopper Center [item]).
        axis: Axis of rotation (Grasshopper Axis [item]).

    Outputs:
        geometry: Rotated geometry (Grasshopper Geometry).
        transform: Transformation data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Euclidean > Rotate 3D (Rot3D).
        pyhopper decisions: angle in radians about the axis through the centre; without geometry only the transform
        is emitted (Grasshopper marks the geometry optional); Grasshopper defaults angle pi/2,
        centre origin, axis Z.
    """

    display_name = "Rotate 3D"
    nickname = "Rot3D"
    gh_guid = "3dfb9a77-6e05-4016-9f20-94f78607d672"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM, optional=True),
        InputParam("angle", float, Access.ITEM, default=math.pi / 2),
        InputParam("center", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("axis", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
    ]
    outputs = [
        OutputParam("geometry", GEOMETRY),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, angle=math.pi / 2, center=AtomicPoint.origin(), axis=AtomicVector.unit_z()):
        xform = AtomicTransform.rotation(center, axis, float(angle))
        return (Component.NO_OUTPUT if geometry is None else apply_transform(xform, geometry)), xform
