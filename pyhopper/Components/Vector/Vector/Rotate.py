"""Rotate - Rotate a vector around an axis."""

import math

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Rotate(Component):
    """Rotate a vector around an axis by an angle in radians."""

    inputs = [
        InputParam("vector", AtomicVector, Access.ITEM),
        InputParam("axis", AtomicVector, Access.ITEM),
        InputParam("angle", float, Access.ITEM, default=0.0),
    ]
    outputs = [OutputParam("vector", AtomicVector)]

    def generate(self, vector=None, axis=None, angle=0.0):
        unit_axis = axis.unitize()
        angle_value = float(angle)
        cos_angle = math.cos(angle_value)
        sin_angle = math.sin(angle_value)
        dot = (
            unit_axis.x * vector.x +
            unit_axis.y * vector.y +
            unit_axis.z * vector.z
        )

        return AtomicVector(
            vector.x * cos_angle + (unit_axis.y * vector.z - unit_axis.z * vector.y) * sin_angle + unit_axis.x * dot * (1.0 - cos_angle),
            vector.y * cos_angle + (unit_axis.z * vector.x - unit_axis.x * vector.z) * sin_angle + unit_axis.y * dot * (1.0 - cos_angle),
            vector.z * cos_angle + (unit_axis.x * vector.y - unit_axis.y * vector.x) * sin_angle + unit_axis.z * dot * (1.0 - cos_angle),
        )
