"""Polygon (polyline) measures used by Polygon Center, verified against Grasshopper 8."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicPolyline
from pyhopper.Utils.Vectors import cross, distance, dot, sub, unit

_TOLERANCE = 1e-12


def _mean(points: list[AtomicPoint]) -> AtomicPoint:
    count = len(points)
    return AtomicPoint(sum(p.x for p in points) / count, sum(p.y for p in points) / count, sum(p.z for p in points) / count)


def polygon_centres(polyline: AtomicPolyline) -> tuple[AtomicPoint, AtomicPoint, AtomicPoint | None]:
    """(vertex centre, edge centre, area centre) of a polyline.

    The vertex centre averages the distinct vertices (a closing duplicate does
    not count twice), the edge centre averages edge midpoints weighted by edge
    length, and the area centre is the planar area centroid — ``None`` for an
    open polyline, which encloses no area.
    """
    if not isinstance(polyline, AtomicPolyline):
        raise TypeError(f"Polygon Center needs a polyline, got {type(polyline).__name__}")
    points = list(polyline.points)
    if len(points) < 2:
        raise ValueError("Polygon Center needs a polyline with at least two points")
    closed = polyline.is_closed
    vertices = points[:-1] if closed and distance(points[0], points[-1]) <= _TOLERANCE else points
    vertex_centre = _mean(vertices)

    weighted = [0.0, 0.0, 0.0]
    total = 0.0
    for start, end in zip(points, points[1:]):
        length = distance(start, end)
        weighted[0] += (start.x + end.x) / 2.0 * length
        weighted[1] += (start.y + end.y) / 2.0 * length
        weighted[2] += (start.z + end.z) / 2.0 * length
        total += length
    edge_centre = vertex_centre if total <= _TOLERANCE else AtomicPoint(weighted[0] / total, weighted[1] / total, weighted[2] / total)

    if not closed:
        return vertex_centre, edge_centre, None
    return vertex_centre, edge_centre, area_centroid(vertices)


def area_centroid(vertices: list[AtomicPoint]) -> AtomicPoint:
    """Centroid of the planar polygon spanned by ``vertices`` (fan triangulation, signed areas)."""
    origin = vertices[0]
    normal_accumulator = [0.0, 0.0, 0.0]
    for a, b in zip(vertices[1:], vertices[2:]):
        n = cross(sub(a, origin), sub(b, origin))
        normal_accumulator[0] += n.x
        normal_accumulator[1] += n.y
        normal_accumulator[2] += n.z
    normal = unit(AtomicPoint(*normal_accumulator)) if any(abs(c) > _TOLERANCE for c in normal_accumulator) else None
    if normal is None:
        return _mean(vertices)
    weighted = [0.0, 0.0, 0.0]
    total = 0.0
    for a, b in zip(vertices[1:], vertices[2:]):
        signed_area = dot(cross(sub(a, origin), sub(b, origin)), normal) / 2.0
        centroid = ((origin.x + a.x + b.x) / 3.0, (origin.y + a.y + b.y) / 3.0, (origin.z + a.z + b.z) / 3.0)
        for axis in range(3):
            weighted[axis] += centroid[axis] * signed_area
        total += signed_area
    if abs(total) <= _TOLERANCE:
        return _mean(vertices)
    return AtomicPoint(weighted[0] / total, weighted[1] / total, weighted[2] / total)
