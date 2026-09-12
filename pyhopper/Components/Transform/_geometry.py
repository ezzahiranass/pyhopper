"""Helpers for the Transform components that need more than an AtomicTransform factory.

Reference points for Move Away From, the angle shear of Shear Angle and the
kaleidoscope image set, all with the conventions read off Grasshopper 8.
"""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicBox, AtomicCircle, AtomicLine, AtomicPlane, AtomicPoint, AtomicPolyline, AtomicRectangle, AtomicTransform, AtomicVector
from pyhopper.Utils.Bounds import box_from_extents, geometry_extents
from pyhopper.Utils.Planes import plane_coordinates, point_on_plane
from pyhopper.Utils.Vectors import cross, distance, dot, sub, translate


def geometry_centre(geometry) -> AtomicPoint:
    """World bounding-box centre of any geometry atom (the point itself for a point)."""
    if isinstance(geometry, AtomicPoint):
        return geometry
    extents = geometry_extents(geometry, AtomicPlane.world_xy())
    if extents is None:
        raise ValueError(f"Cannot locate a {type(geometry).__name__}")
    return box_from_extents(AtomicPlane.world_xy(), extents).plane.origin


def _closest_on_segment(start: AtomicPoint, end: AtomicPoint, point: AtomicPoint) -> AtomicPoint:
    direction = sub(end, start)
    span = dot(direction, direction)
    if span <= 1e-24:
        return start
    t = min(max(dot(sub(point, start), direction) / span, 0.0), 1.0)
    return translate(start, direction, t)


def closest_point_on(emitter, point: AtomicPoint) -> AtomicPoint:
    """Closest point of ``emitter`` to ``point`` — exact for points, lines, polylines, rectangles, circles,
    boxes and planes (Grasshopper measures a plane as the square [-1, 1]² on it); other curves, surfaces
    and breps go through the closest-point kernel, anything else answers with its bounding-box centre."""
    if isinstance(emitter, AtomicPoint):
        return emitter
    if isinstance(emitter, AtomicLine):
        return _closest_on_segment(emitter.start, emitter.end, point)
    if isinstance(emitter, AtomicPolyline):
        return min((_closest_on_segment(a, b, point) for a, b in zip(emitter.points, emitter.points[1:])), key=lambda candidate: distance(candidate, point))
    if isinstance(emitter, AtomicRectangle):
        corners = [point_on_plane(emitter.plane, sx * float(emitter.x_size) / 2.0, sy * float(emitter.y_size) / 2.0) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        return min((_closest_on_segment(a, b, point) for a, b in zip(corners, corners[1:] + corners[:1])), key=lambda candidate: distance(candidate, point))
    if isinstance(emitter, AtomicCircle):
        x, y, _ = plane_coordinates(emitter.plane, point)
        radial = math.hypot(x, y)
        if radial <= 1e-12:
            return point_on_plane(emitter.plane, float(emitter.radius), 0.0)
        return point_on_plane(emitter.plane, x / radial * float(emitter.radius), y / radial * float(emitter.radius))
    if isinstance(emitter, AtomicBox):
        x, y, z = plane_coordinates(emitter.plane, point)
        hx, hy, hz = float(emitter.x_size) / 2.0, float(emitter.y_size) / 2.0, float(emitter.z_size) / 2.0
        return point_on_plane(emitter.plane, min(max(x, -hx), hx), min(max(y, -hy), hy), min(max(z, -hz), hz))
    if isinstance(emitter, AtomicPlane):
        x, y, _ = plane_coordinates(emitter, point)
        return point_on_plane(emitter, min(max(x, -1.0), 1.0), min(max(y, -1.0), 1.0))
    from pyhopper.Utils.ClosestPoints import geometry_closest_point

    try:
        return geometry_closest_point(emitter, point)[0]
    except TypeError:
        return geometry_centre(emitter)


def move_away_translation(geometry, emitter, distance_along: float) -> AtomicVector:
    """Translation moving ``geometry`` ``distance_along`` away from ``emitter``.

    Grasshopper-verified: the direction runs from the emitter's closest point to the geometry's
    reference point (its bounding-box centre) to that reference point.
    """
    reference = geometry_centre(geometry)
    direction = sub(reference, closest_point_on(emitter, reference))
    length = math.sqrt(dot(direction, direction))
    if length <= 1e-12:
        return AtomicVector(0.0, 0.0, 0.0)
    factor = float(distance_along) / length
    return AtomicVector(direction.x * factor, direction.y * factor, direction.z * factor)


def shear_by_angles(base: AtomicPlane, angle_x: float, angle_y: float) -> AtomicTransform:
    """Grasshopper's Shear Angle: the base plane's z axis tilts by ``angle_x`` about x, then ``angle_y`` about y."""
    ax, ay = float(angle_x), float(angle_y)
    # Ry(ay) · Rx(ax) · (0, 0, 1) in plane coordinates
    tilted = (math.cos(ax) * math.sin(ay), -math.sin(ax), math.cos(ax) * math.cos(ay))
    if abs(tilted[2]) <= 1e-12:
        raise ValueError("Shear Angle needs tilt angles below 90 degrees")
    in_plane = AtomicTransform._from_linear(((1.0, 0.0, tilted[0]), (0.0, 1.0, tilted[1]), (0.0, 0.0, tilted[2])), (0.0, 0.0, 0.0))
    to_plane = AtomicTransform.plane_to_plane(AtomicPlane.world_xy(), base)
    return AtomicTransform.compound([to_plane.inverse(), in_plane, to_plane])


def kaleidoscope_transforms(plane: AtomicPlane, segments: int, reference: AtomicPoint) -> list[AtomicTransform]:
    """The ``segments`` kaleidoscope images: even images rotate by k·2π/S about the plane normal, odd
    images mirror across the line through the origin at ``φ + k·π/S`` where φ is the reference
    point's angle in the plane (Grasshopper-verified)."""
    count = int(segments)
    if count < 1:
        raise ValueError("Kaleidoscope needs at least one segment")
    x, y, _ = plane_coordinates(plane, reference)
    phi = math.atan2(y, x)
    images = []
    for k in range(count):
        if k % 2 == 0:
            images.append(AtomicTransform.rotation(plane.origin, plane.normal, k * 2.0 * math.pi / count))
        else:
            theta = phi + k * math.pi / count
            mirror_direction = AtomicVector(
                plane.x_axis.x * math.cos(theta) + plane.y_axis.x * math.sin(theta),
                plane.x_axis.y * math.cos(theta) + plane.y_axis.y * math.sin(theta),
                plane.x_axis.z * math.cos(theta) + plane.y_axis.z * math.sin(theta),
            )
            images.append(AtomicTransform.reflection(AtomicPlane(plane.origin, cross(plane.normal, mirror_direction), mirror_direction)))
    return images

