"""Rotate - Rotate an object in a plane."""

import math

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform


class Rotate(Component):
    """Rotate geometry around a plane's origin and normal axis.

    Accepts any geometry atom, a rotation angle in radians, and a plane
    whose origin is the center of rotation and whose normal is the axis.
    Returns the rotated geometry and the corresponding transformation matrix.
    """

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("angle", float, Access.ITEM, default=math.pi / 2),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, angle=math.pi / 2, plane=AtomicPlane.world_xy()):
        xform = AtomicTransform.rotation(plane.origin, plane.normal, float(angle))
        return apply_transform(xform, geometry), xform
