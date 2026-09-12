"""Ellipse - Create an ellipse from a plane and two radii."""

import math

from pyhopper.Core.Atoms import AtomicEllipse, AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _point_along(origin: AtomicPoint, axis: AtomicVector, distance: float) -> AtomicPoint:
    return AtomicPoint(
        origin.x + axis.x * distance,
        origin.y + axis.y * distance,
        origin.z + axis.z * distance,
    )


class Ellipse(Component):
    """Create an ``AtomicEllipse`` and return its two focus points."""

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("radius_1", float, Access.ITEM, default=1.0),
        InputParam("radius_2", float, Access.ITEM, default=0.5),
    ]
    outputs = [
        OutputParam("ellipse", AtomicEllipse),
        OutputParam("focus_1", AtomicPoint),
        OutputParam("focus_2", AtomicPoint),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), radius_1=1.0, radius_2=0.5):
        radius_x = abs(float(radius_1))
        radius_y = abs(float(radius_2))
        if radius_x <= 0.0 or radius_y <= 0.0:
            raise ValueError("Ellipse radii must be greater than zero")

        if radius_x >= radius_y:
            focus_axis = plane.x_axis.unitize()
            focus_distance = math.sqrt(radius_x * radius_x - radius_y * radius_y)
        else:
            focus_axis = plane.y_axis.unitize()
            focus_distance = math.sqrt(radius_y * radius_y - radius_x * radius_x)

        ellipse = AtomicEllipse(plane=plane, radius_x=radius_x, radius_y=radius_y)
        return (
            ellipse,
            _point_along(plane.origin, focus_axis, focus_distance),
            _point_along(plane.origin, focus_axis, -focus_distance),
        )
