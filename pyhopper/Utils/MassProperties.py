"""Area and volume mass-property utilities."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import (
    AtomicBrep,
    AtomicBox,
    AtomicCircle,
    AtomicCylinder,
    AtomicEllipse,
    AtomicMesh,
    AtomicPoint,
    AtomicPolyline,
    AtomicRectangle,
    AtomicSurface,
)
from pyhopper.Utils.Curves import evaluate_nurbs_curve, nurbs_curve_domain
from pyhopper.Utils.Surfaces import surface_integration_triangles
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


_TOLERANCE = 1e-10


def _vector(a, b):
    return b[0] - a[0], b[1] - a[1], b[2] - a[2]


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _triangle_area_centroid(a, b, c):
    cross = _cross(_vector(a, b), _vector(a, c))
    area = math.sqrt(_dot(cross, cross)) / 2.0
    return area, (
        (a[0] + b[0] + c[0]) / 3.0,
        (a[1] + b[1] + c[1]) / 3.0,
        (a[2] + b[2] + c[2]) / 3.0,
    )


def _triangles(positions, indices):
    return [
        (positions[indices[index]], positions[indices[index + 1]], positions[indices[index + 2]])
        for index in range(0, len(indices), 3)
    ]


def _surface_triangles(surface: AtomicSurface):
    return surface_integration_triangles(surface)


def _mesh_triangles(mesh: AtomicMesh):
    positions = [(point.x, point.y, point.z) for point in mesh.vertices]
    indices = []
    for face in mesh.faces:
        for index in range(1, len(face) - 1):
            indices.extend((face[0], face[index], face[index + 1]))
    return _triangles(positions, indices)


def _curve_integration_points(geometry) -> tuple[AtomicPoint, ...]:
    curve = as_nurbs_curve(geometry)
    start, end = nurbs_curve_domain(curve)
    sample_count = max(64, len(curve.control_points) * 12)
    return tuple(
        evaluate_nurbs_curve(curve, start + (end - start) * index / sample_count)
        for index in range(sample_count + 1)
    )


def _geometry_triangles(geometry):
    if isinstance(geometry, AtomicBox):
        from pyhopper.Utils.Boxes import box_to_brep

        return _geometry_triangles(box_to_brep(geometry))
    if isinstance(geometry, AtomicSurface):
        return _surface_triangles(geometry)
    if isinstance(geometry, AtomicMesh):
        return _mesh_triangles(geometry)
    if isinstance(geometry, AtomicBrep):
        return [triangle for face in geometry.faces for triangle in _surface_triangles(face)]
    raise TypeError(f"Mass properties do not support {type(geometry).__name__}")


def _weighted_centroid(weighted_centroids, total):
    if total <= _TOLERANCE:
        raise ValueError("Geometry has no measurable area or volume")
    return AtomicPoint(
        sum(weight * centroid[0] for weight, centroid in weighted_centroids) / total,
        sum(weight * centroid[1] for weight, centroid in weighted_centroids) / total,
        sum(weight * centroid[2] for weight, centroid in weighted_centroids) / total,
    )


def _triangle_area_properties(triangles):
    weighted = []
    total = 0.0
    for a, b, c in triangles:
        area, centroid = _triangle_area_centroid(a, b, c)
        if area > _TOLERANCE:
            total += area
            weighted.append((area, centroid))
    return total, _weighted_centroid(weighted, total)


def _closed_polyline_properties(points: tuple[AtomicPoint, ...]):
    if len(points) < 4:
        raise ValueError("Area requires a closed planar curve")
    seam_distance = math.sqrt(
        (points[0].x - points[-1].x) ** 2
        + (points[0].y - points[-1].y) ** 2
        + (points[0].z - points[-1].z) ** 2
    )
    if seam_distance > 1e-8:
        raise ValueError("Area requires a closed planar curve")
    points = points[:-1] + (points[0],)
    coordinates = [(point.x, point.y, point.z) for point in points]
    origin = coordinates[0]
    normal = (0.0, 0.0, 0.0)
    for index in range(1, len(coordinates) - 2):
        candidate = _cross(_vector(origin, coordinates[index]), _vector(origin, coordinates[index + 1]))
        length = math.sqrt(_dot(candidate, candidate))
        if length > _TOLERANCE:
            normal = tuple(value / length for value in candidate)
            break
    if normal == (0.0, 0.0, 0.0):
        raise ValueError("Geometry has no measurable area")
    if any(abs(_dot(_vector(origin, point), normal)) > 1e-8 for point in coordinates[1:]):
        raise ValueError("Area requires a planar closed curve")

    signed_total = 0.0
    weighted = [0.0, 0.0, 0.0]
    for index in range(1, len(coordinates) - 2):
        a, b, c = origin, coordinates[index], coordinates[index + 1]
        signed_area = _dot(_cross(_vector(a, b), _vector(a, c)), normal) / 2.0
        centroid = tuple((a[axis] + b[axis] + c[axis]) / 3.0 for axis in range(3))
        signed_total += signed_area
        for axis in range(3):
            weighted[axis] += signed_area * centroid[axis]
    if abs(signed_total) <= _TOLERANCE:
        raise ValueError("Geometry has no measurable area")
    return abs(signed_total), AtomicPoint(*(value / signed_total for value in weighted))


def area_properties(geometry) -> tuple[float, AtomicPoint]:
    """Return area and area centroid for supported geometry."""
    if isinstance(geometry, AtomicCircle):
        return math.pi * geometry.radius * geometry.radius, geometry.center
    if isinstance(geometry, AtomicEllipse):
        return math.pi * geometry.radius_x * geometry.radius_y, geometry.plane.origin
    if isinstance(geometry, AtomicRectangle):
        return abs(geometry.x_size * geometry.y_size), geometry.plane.origin
    if isinstance(geometry, AtomicBox):
        x, y, z = abs(geometry.x_size), abs(geometry.y_size), abs(geometry.z_size)
        return 2.0 * (x * y + x * z + y * z), geometry.plane.origin
    if isinstance(geometry, AtomicCylinder):
        radius = abs(geometry.radius)
        height = abs(geometry.height)
        centroid = AtomicPoint(
            geometry.plane.origin.x + geometry.plane.normal.x * geometry.height / 2.0,
            geometry.plane.origin.y + geometry.plane.normal.y * geometry.height / 2.0,
            geometry.plane.origin.z + geometry.plane.normal.z * geometry.height / 2.0,
        )
        return 2.0 * math.pi * radius * (radius + height), centroid
    if isinstance(geometry, AtomicPolyline):
        return _closed_polyline_properties(geometry.points)
    if not isinstance(geometry, (AtomicSurface, AtomicMesh, AtomicBrep)):
        return _closed_polyline_properties(_curve_integration_points(geometry))
    return _triangle_area_properties(_geometry_triangles(geometry))


def _point_key(point):
    return tuple(round(value, 8) for value in point)


def _is_closed_triangles(triangles) -> bool:
    edge_counts = {}
    for triangle in triangles:
        area, _ = _triangle_area_centroid(*triangle)
        if area <= _TOLERANCE:
            continue
        keys = [_point_key(point) for point in triangle]
        for start, end in ((keys[0], keys[1]), (keys[1], keys[2]), (keys[2], keys[0])):
            edge = tuple(sorted((start, end)))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    return bool(edge_counts) and all(count == 2 for count in edge_counts.values())


def volume_properties(geometry) -> tuple[float, AtomicPoint]:
    """Return numerical volume and centroid for closed Breps, meshes, and surfaces."""
    if isinstance(geometry, AtomicBox):
        return abs(geometry.x_size * geometry.y_size * geometry.z_size), geometry.plane.origin
    if isinstance(geometry, AtomicCylinder):
        centroid = AtomicPoint(
            geometry.plane.origin.x + geometry.plane.normal.x * geometry.height / 2.0,
            geometry.plane.origin.y + geometry.plane.normal.y * geometry.height / 2.0,
            geometry.plane.origin.z + geometry.plane.normal.z * geometry.height / 2.0,
        )
        return math.pi * geometry.radius * geometry.radius * abs(geometry.height), centroid
    if not isinstance(geometry, (AtomicBrep, AtomicMesh, AtomicSurface)):
        raise TypeError("Volume supports closed AtomicBrep, AtomicMesh, AtomicSurface, or AtomicCylinder geometry")
    triangles = _geometry_triangles(geometry)
    if not isinstance(geometry, AtomicBrep) and not _is_closed_triangles(triangles):
        raise ValueError("Volume requires closed geometry")

    vertices = [point for triangle in triangles for point in triangle]
    reference = tuple(sum(point[index] for point in vertices) / len(vertices) for index in range(3))
    weighted = []
    total = 0.0
    for a, b, c in triangles:
        ar = _vector(reference, a)
        br = _vector(reference, b)
        cr = _vector(reference, c)
        volume = abs(_dot(ar, _cross(br, cr))) / 6.0
        if volume <= _TOLERANCE:
            continue
        centroid = tuple((reference[index] + a[index] + b[index] + c[index]) / 4.0 for index in range(3))
        total += volume
        weighted.append((volume, centroid))
    return total, _weighted_centroid(weighted, total)
