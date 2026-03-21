"""Rectangle - Create a rectangle from plane and side lengths."""

import math

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Atoms import AtomicPoint, AtomicPolyline
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _point_on_plane(plane: AtomicPlane, x: float, y: float) -> AtomicPoint:
    x_axis = plane.x_axis
    y_axis = plane.y_axis
    origin = plane.origin
    return AtomicPoint(
        origin.x + x_axis.x * x + y_axis.x * y,
        origin.y + x_axis.y * x + y_axis.y * y,
        origin.z + x_axis.z * x + y_axis.z * y,
    )


class Rectangle(Component):
    """Create an ``AtomicPolyline`` rectangle from a plane and side lengths.

    Returns the rectangle outline and its perimeter length. A non-zero radius
    produces a rounded rectangle approximation.
    """

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("x_size", float, Access.ITEM, default=1.0),
        InputParam("y_size", float, Access.ITEM, default=1.0),
        InputParam("radius", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("rectangle"),
        OutputParam("length", float),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), x_size=1.0, y_size=1.0, radius=0.0):
        half_x = abs(float(x_size)) / 2.0
        half_y = abs(float(y_size)) / 2.0
        fillet = max(0.0, min(float(radius), half_x, half_y))

        if fillet == 0.0:
            local_points = [
                (-half_x, -half_y),
                (half_x, -half_y),
                (half_x, half_y),
                (-half_x, half_y),
                (-half_x, -half_y),
            ]
            perimeter = 2.0 * (abs(float(x_size)) + abs(float(y_size)))
        else:
            corner_segments = 6
            local_points = []
            corner_specs = [
                ((half_x - fillet, half_y - fillet), 0.0, math.pi / 2.0),
                ((-half_x + fillet, half_y - fillet), math.pi / 2.0, math.pi),
                ((-half_x + fillet, -half_y + fillet), math.pi, 3.0 * math.pi / 2.0),
                ((half_x - fillet, -half_y + fillet), 3.0 * math.pi / 2.0, 2.0 * math.pi),
            ]

            for (cx, cy), start_angle, end_angle in corner_specs:
                for step in range(corner_segments + 1):
                    t = step / corner_segments
                    angle = start_angle + (end_angle - start_angle) * t
                    local_points.append((
                        cx + math.cos(angle) * fillet,
                        cy + math.sin(angle) * fillet,
                    ))

            local_points.append(local_points[0])
            perimeter = (
                2.0 * (abs(float(x_size)) + abs(float(y_size)) - (4.0 * fillet))
                + 2.0 * math.pi * fillet
            )

        points = tuple(_point_on_plane(plane, x, y) for x, y in local_points)
        return AtomicPolyline(points=points), perimeter
