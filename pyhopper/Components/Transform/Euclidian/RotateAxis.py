"""RotateAxis - Rotate geometry around a line axis."""

import math

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform


class RotateAxis(Component):
    """Rotate geometry around an arbitrary line axis."""

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("angle", float, Access.ITEM, default=math.pi / 2.0),
        InputParam(
            "axis",
            AtomicLine,
            Access.ITEM,
            default=AtomicLine(AtomicPoint.origin(), AtomicPoint(0.0, 0.0, 1.0)),
        ),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(
        self,
        geometry=None,
        angle=math.pi / 2.0,
        axis=AtomicLine(AtomicPoint.origin(), AtomicPoint(0.0, 0.0, 1.0)),
    ):
        if axis.length == 0.0:
            raise ValueError("RotateAxis axis must have non-zero length")
        xform = AtomicTransform.rotation(axis.start, axis.direction, float(angle))
        return apply_transform(xform, geometry), xform
