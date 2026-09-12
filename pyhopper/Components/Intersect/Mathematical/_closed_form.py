"""Closed-form intersections of infinite lines and planes (Grasshopper Intersect › Mathematical).

Conventions verified against Grasshopper 8:

* lines are infinite; parameters are normalised along each segment (0 at the
  start, 1 at the end, values outside that range beyond the segment);
* ``Line | Line`` returns the closest points of skew lines; (anti)parallel
  lines have no result;
* ``Line | Plane`` also reports the intersection in plane coordinates;
* ``Plane | Plane`` returns a unit-length line: it starts at the projection of
  the midpoint of the two plane origins onto the intersection line and runs
  along ``normal_b x normal_a``.
"""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicLine, AtomicPlane, AtomicPoint
from pyhopper.Utils.Planes import plane_coordinates
from pyhopper.Utils.Vectors import cross, dot, is_zero, scale, sub, translate, unit

_PARALLEL = 1e-12


def line_line_closest_points(line_a: AtomicLine, line_b: AtomicLine) -> tuple[float, float, AtomicPoint, AtomicPoint] | None:
    """(t_a, t_b, point_a, point_b) of the closest approach, or None when the lines are (anti)parallel."""
    u = sub(line_a.end, line_a.start)
    v = sub(line_b.end, line_b.start)
    w = sub(line_a.start, line_b.start)
    a, b, c = dot(u, u), dot(u, v), dot(v, v)
    d, e = dot(u, w), dot(v, w)
    denominator = a * c - b * b
    if a <= _PARALLEL or c <= _PARALLEL or abs(denominator) <= _PARALLEL * a * c:
        return None
    t_a = (b * e - c * d) / denominator
    t_b = (a * e - b * d) / denominator
    return t_a, t_b, translate(line_a.start, u, t_a), translate(line_b.start, v, t_b)


def line_plane_intersection(line: AtomicLine, plane: AtomicPlane) -> tuple[AtomicPoint, float, AtomicPoint] | None:
    """(point, line parameter, plane coordinates as a point) or None when the line is parallel to the plane."""
    direction = sub(line.end, line.start)
    slope = dot(direction, plane.normal)
    if abs(slope) <= _PARALLEL * max(1.0, dot(direction, direction)):
        return None
    t = dot(sub(plane.origin, line.start), plane.normal) / slope
    point = translate(line.start, direction, t)
    u, v, _ = plane_coordinates(plane, point)
    return point, t, AtomicPoint(u, v, 0.0)


def plane_plane_intersection(plane_a: AtomicPlane, plane_b: AtomicPlane) -> AtomicLine | None:
    """Unit-length intersection line, or None for parallel planes."""
    direction = cross(plane_b.normal, plane_a.normal)
    if is_zero(direction, _PARALLEL):
        return None
    direction = unit(direction)
    # a point on both planes: solve for the point closest to the origins' midpoint
    midpoint = AtomicPoint(
        (plane_a.origin.x + plane_b.origin.x) / 2.0,
        (plane_a.origin.y + plane_b.origin.y) / 2.0,
        (plane_a.origin.z + plane_b.origin.z) / 2.0,
    )
    point = _closest_point_on_both_planes(midpoint, plane_a, plane_b, direction)
    return AtomicLine(point, translate(point, direction))


def _closest_point_on_both_planes(seed: AtomicPoint, plane_a: AtomicPlane, plane_b: AtomicPlane, direction) -> AtomicPoint:
    """Project ``seed`` onto the intersection line of two planes (moving only across the line)."""
    n_a, n_b = plane_a.normal, plane_b.normal
    d_a = dot(sub(plane_a.origin, seed), n_a)  # signed offsets of the seed from each plane
    d_b = dot(sub(plane_b.origin, seed), n_b)
    # move within the plane perpendicular to the line: seed + x n_a + y n_b, with both plane equations satisfied
    aa, ab, bb = dot(n_a, n_a), dot(n_a, n_b), dot(n_b, n_b)
    determinant = aa * bb - ab * ab
    x = (d_a * bb - d_b * ab) / determinant
    y = (d_b * aa - d_a * ab) / determinant
    moved = translate(seed, scale(n_a, x))
    moved = translate(moved, scale(n_b, y))
    return moved
