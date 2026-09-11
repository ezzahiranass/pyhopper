"""OffsetCurve - Offset a planar curve with configurable corner joins."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicLine,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicRectangle,
)
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE


_TOLERANCE = 1e-9
_JOIN_SEGMENTS = 8


def _to_local(plane: AtomicPlane, point: AtomicPoint) -> tuple[float, float, float]:
    delta = (
        point.x - plane.origin.x,
        point.y - plane.origin.y,
        point.z - plane.origin.z,
    )
    return (
        delta[0] * plane.x_axis.x + delta[1] * plane.x_axis.y + delta[2] * plane.x_axis.z,
        delta[0] * plane.y_axis.x + delta[1] * plane.y_axis.y + delta[2] * plane.y_axis.z,
        delta[0] * plane.normal.x + delta[1] * plane.normal.y + delta[2] * plane.normal.z,
    )


def _from_local(plane: AtomicPlane, point: tuple[float, float]) -> AtomicPoint:
    x, y = point
    return AtomicPoint(
        plane.origin.x + plane.x_axis.x * x + plane.y_axis.x * y,
        plane.origin.y + plane.x_axis.y * x + plane.y_axis.y * y,
        plane.origin.z + plane.x_axis.z * x + plane.y_axis.z * y,
    )


def _unit(vector: tuple[float, float]) -> tuple[float, float]:
    length = math.hypot(*vector)
    if length <= _TOLERANCE:
        raise ValueError("Offset Curve requires non-zero-length curve segments")
    return vector[0] / length, vector[1] / length


def _line_intersection(
    point_a: tuple[float, float],
    direction_a: tuple[float, float],
    point_b: tuple[float, float],
    direction_b: tuple[float, float],
) -> tuple[float, float] | None:
    denominator = direction_a[0] * direction_b[1] - direction_a[1] * direction_b[0]
    if abs(denominator) <= _TOLERANCE:
        return None
    delta = (point_b[0] - point_a[0], point_b[1] - point_a[1])
    scale = (delta[0] * direction_b[1] - delta[1] * direction_b[0]) / denominator
    return point_a[0] + direction_a[0] * scale, point_a[1] + direction_a[1] * scale


def _arc_join(
    center: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
    turn: float,
) -> list[tuple[float, float]]:
    start_angle = math.atan2(start[1] - center[1], start[0] - center[0])
    end_angle = math.atan2(end[1] - center[1], end[0] - center[0])
    if turn > 0.0:
        while end_angle <= start_angle:
            end_angle += 2.0 * math.pi
    else:
        while end_angle >= start_angle:
            end_angle -= 2.0 * math.pi
    return [
        (
            center[0] + math.cos(start_angle + (end_angle - start_angle) * step / _JOIN_SEGMENTS)
            * math.hypot(start[0] - center[0], start[1] - center[1]),
            center[1] + math.sin(start_angle + (end_angle - start_angle) * step / _JOIN_SEGMENTS)
            * math.hypot(start[0] - center[0], start[1] - center[1]),
        )
        for step in range(_JOIN_SEGMENTS + 1)
    ]


def _smooth_join(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
) -> list[tuple[float, float]]:
    return [
        (
            (1.0 - t) ** 2 * start[0] + 2.0 * (1.0 - t) * t * control[0] + t**2 * end[0],
            (1.0 - t) ** 2 * start[1] + 2.0 * (1.0 - t) * t * control[1] + t**2 * end[1],
        )
        for t in (step / _JOIN_SEGMENTS for step in range(_JOIN_SEGMENTS + 1))
    ]


def _rectangle_points(rectangle: AtomicRectangle) -> tuple[AtomicPoint, ...]:
    half_x = abs(float(rectangle.x_size)) / 2.0
    half_y = abs(float(rectangle.y_size)) / 2.0
    local = ((-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y))
    points = tuple(_from_local(rectangle.plane, point) for point in local)
    return points + (points[0],)


def _offset_polyline(
    curve: AtomicPolyline,
    distance: float,
    plane: AtomicPlane,
    corners: int,
):
    if len(curve.points) < 2:
        raise ValueError("Offset Curve requires a polyline with at least two points")

    closed = curve.is_closed
    source_points = curve.points[:-1] if closed else curve.points
    local_points = []
    for point in source_points:
        x, y, z = _to_local(plane, point)
        if abs(z) > _TOLERANCE:
            raise ValueError("Offset Curve requires the input curve to lie in the offset plane")
        local_points.append((x, y))

    segment_pairs = list(zip(local_points, local_points[1:]))
    if closed:
        segment_pairs.append((local_points[-1], local_points[0]))
    directions = [_unit((end[0] - start[0], end[1] - start[1])) for start, end in segment_pairs]
    shifted = [
        (
            (start[0] - direction[1] * distance, start[1] + direction[0] * distance),
            (end[0] - direction[1] * distance, end[1] + direction[0] * distance),
        )
        for (start, end), direction in zip(segment_pairs, directions)
    ]

    if corners == 0:
        return [
            AtomicLine(_from_local(plane, start), _from_local(plane, end))
            for start, end in shifted
        ]

    result: list[tuple[float, float]] = []
    join_indices = range(len(local_points)) if closed else range(1, len(local_points) - 1)
    if not closed:
        result.append(shifted[0][0])

    for vertex_index in join_indices:
        previous_index = (vertex_index - 1) % len(shifted)
        next_index = vertex_index % len(shifted)
        previous_end = shifted[previous_index][1]
        next_start = shifted[next_index][0]
        previous_direction = directions[previous_index]
        next_direction = directions[next_index]
        intersection = _line_intersection(
            previous_end,
            previous_direction,
            next_start,
            next_direction,
        )
        turn = (
            previous_direction[0] * next_direction[1]
            - previous_direction[1] * next_direction[0]
        )

        if corners == 1:
            join = [intersection or previous_end]
        elif corners == 2 and abs(turn) > _TOLERANCE and abs(distance) > _TOLERANCE:
            join = _arc_join(local_points[vertex_index], previous_end, next_start, turn)
        elif corners == 3 and intersection is not None:
            join = _smooth_join(previous_end, intersection, next_start)
        else:
            join = [previous_end, next_start]

        result.extend(join if not result else join[1:] if result[-1] == join[0] else join)

    if not closed:
        result.append(shifted[-1][1])
    elif result and result[0] != result[-1]:
        result.append(result[0])

    return AtomicPolyline(tuple(_from_local(plane, point) for point in result))


def _offset_line(curve: AtomicLine, distance: float, plane: AtomicPlane) -> AtomicLine:
    start_x, start_y, start_z = _to_local(plane, curve.start)
    end_x, end_y, end_z = _to_local(plane, curve.end)
    if abs(start_z) > _TOLERANCE or abs(end_z) > _TOLERANCE:
        raise ValueError("Offset Curve requires the input curve to lie in the offset plane")
    direction = _unit((end_x - start_x, end_y - start_y))
    shift = (-direction[1] * distance, direction[0] * distance)
    return AtomicLine(
        _from_local(plane, (start_x + shift[0], start_y + shift[1])),
        _from_local(plane, (end_x + shift[0], end_y + shift[1])),
    )


def _normal_alignment(curve_plane: AtomicPlane, offset_plane: AtomicPlane) -> float:
    alignment = (
        curve_plane.normal.x * offset_plane.normal.x
        + curve_plane.normal.y * offset_plane.normal.y
        + curve_plane.normal.z * offset_plane.normal.z
    )
    if abs(abs(alignment) - 1.0) > _TOLERANCE:
        raise ValueError("Offset Curve requires the curve plane to be parallel to the offset plane")
    _, _, height = _to_local(offset_plane, curve_plane.origin)
    if abs(height) > _TOLERANCE:
        raise ValueError("Offset Curve requires the input curve to lie in the offset plane")
    return 1.0 if alignment >= 0.0 else -1.0


class OffsetCurve(Component):
    """Offset a planar curve.

    Corner styles follow Grasshopper/Rhino values: 0 None, 1 Sharp, 2 Round,
    3 Smooth, and 4 Chamfer. General NURBS and ellipse offsets require a
    future geometry-kernel adapter and are rejected clearly.
    """

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("distance", float, Access.ITEM, default=1.0),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("corners", int, Access.ITEM, default=0),
    ]
    outputs = [OutputParam("curve", CURVE)]

    def generate(self, curve=None, distance=1.0, plane=AtomicPlane.world_xy(), corners=0):
        offset_distance = float(distance)
        corner_style = int(corners)
        if corner_style not in range(5):
            raise ValueError("Offset Curve corners must be an integer from 0 to 4")

        if isinstance(curve, AtomicLine):
            return _offset_line(curve, offset_distance, plane)

        if isinstance(curve, AtomicRectangle):
            return _offset_polyline(AtomicPolyline(_rectangle_points(curve)), offset_distance, plane, corner_style)

        if isinstance(curve, AtomicPolyline):
            return _offset_polyline(curve, offset_distance, plane, corner_style)

        if isinstance(curve, AtomicCircle):
            radius = float(curve.radius) - offset_distance * _normal_alignment(curve.plane, plane)
            if radius <= _TOLERANCE:
                raise ValueError("Offset Curve distance collapses or reverses the circle")
            return AtomicCircle(curve.plane, radius)

        if isinstance(curve, AtomicArc):
            orientation = 1.0 if curve.angle.length >= 0.0 else -1.0
            radius = float(curve.radius) - offset_distance * orientation * _normal_alignment(curve.plane, plane)
            if radius <= _TOLERANCE:
                raise ValueError("Offset Curve distance collapses or reverses the arc")
            return AtomicArc(curve.plane, radius, curve.angle)

        raise ValueError(
            f"Offset Curve does not yet support exact offsets of {type(curve).__name__}; "
            "a geometry-kernel adapter is required"
        )
