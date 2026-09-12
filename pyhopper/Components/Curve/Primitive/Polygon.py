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


def _rounded_polygon_points(
    radius: float,
    segment_count: int,
    fillet_radius: float,
) -> tuple[tuple[float, float], ...]:
    vertices = tuple(
        (
            math.cos((2.0 * math.pi * index) / segment_count) * radius,
            math.sin((2.0 * math.pi * index) / segment_count) * radius,
        )
        for index in range(segment_count)
    )
    side_length = 2.0 * radius * math.sin(math.pi / segment_count)
    interior_angle = math.pi - (2.0 * math.pi / segment_count)
    maximum_fillet = side_length * 0.5 * math.tan(interior_angle * 0.5)
    fillet = min(max(0.0, fillet_radius), maximum_fillet)
    if fillet == 0.0:
        return vertices + (vertices[0],)

    trim = fillet / math.tan(interior_angle * 0.5)
    center_distance = fillet / math.sin(interior_angle * 0.5)
    corner_segments = 8
    result = []

    for index, vertex in enumerate(vertices):
        previous = vertices[(index - 1) % segment_count]
        following = vertices[(index + 1) % segment_count]
        previous_direction = (
            (previous[0] - vertex[0]) / side_length,
            (previous[1] - vertex[1]) / side_length,
        )
        following_direction = (
            (following[0] - vertex[0]) / side_length,
            (following[1] - vertex[1]) / side_length,
        )
        bisector = (
            previous_direction[0] + following_direction[0],
            previous_direction[1] + following_direction[1],
        )
        bisector_length = math.hypot(*bisector)
        bisector = (bisector[0] / bisector_length, bisector[1] / bisector_length)
        center = (
            vertex[0] + bisector[0] * center_distance,
            vertex[1] + bisector[1] * center_distance,
        )
        start = (
            vertex[0] + previous_direction[0] * trim,
            vertex[1] + previous_direction[1] * trim,
        )
        end = (
            vertex[0] + following_direction[0] * trim,
            vertex[1] + following_direction[1] * trim,
        )
        start_angle = math.atan2(start[1] - center[1], start[0] - center[0])
        end_angle = math.atan2(end[1] - center[1], end[0] - center[0])
        while end_angle <= start_angle:
            end_angle += 2.0 * math.pi
        result.extend(
            (
                center[0] + math.cos(start_angle + (end_angle - start_angle) * step / corner_segments) * fillet,
                center[1] + math.sin(start_angle + (end_angle - start_angle) * step / corner_segments) * fillet,
            )
            for step in range(corner_segments + 1)
        )

    result.append(result[0])
    return tuple(result)


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
        local_points = _rounded_polygon_points(
            polygon_radius,
            segment_count,
            max(0.0, float(fillet_radius)),
        )
        points = tuple(_point_on_plane(plane, x, y) for x, y in local_points)
        return AtomicPolyline(points=points), _polyline_length(points)
