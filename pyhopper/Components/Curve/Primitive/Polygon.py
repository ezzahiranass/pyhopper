"""Polygon - Create a regular polygon from a plane, radius, and segment count."""

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


def _polyline_length(points: tuple[AtomicPoint, ...]) -> float:
    total = 0.0
    for start, end in zip(points, points[1:]):
        dx = end.x - start.x
        dy = end.y - start.y
        dz = end.z - start.z
        total += math.sqrt(dx * dx + dy * dy + dz * dz)
    return total


class Polygon(Component):
    """Create a regular ``AtomicPolyline`` polygon from plane parameters.

    Accepts a plane, radius, segment count, and optional fillet radius, then
    returns the polygon outline and its perimeter length.
    """

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("radius", float, Access.ITEM, default=1.0),
        InputParam("segments", int, Access.ITEM, default=6),
        InputParam("fillet_radius", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("polygon"),
        OutputParam("length", float),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), radius=1.0, segments=6, fillet_radius=0.0):
        segment_count = max(3, int(segments))
        polygon_radius = abs(float(radius))
        _ = max(0.0, float(fillet_radius))

        points = tuple(
            _point_on_plane(
                plane,
                math.cos((2.0 * math.pi * index) / segment_count) * polygon_radius,
                math.sin((2.0 * math.pi * index) / segment_count) * polygon_radius,
            )
            for index in range(segment_count)
        )
        closed = points + (points[0],)
        return AtomicPolyline(points=closed), _polyline_length(closed)
