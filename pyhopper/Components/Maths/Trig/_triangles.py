"""Triangle geometry and trigonometry shared by the Maths > Trig triangle components.

Everything here follows the conventions read off Grasshopper 8: the centre components
emit the construction lines Grasshopper draws (medians, in-triangle bisector segments,
corner-to-edge angle bisectors, foot-to-corner altitudes) and ``solve_triangle`` fills
in unknown angles and sides without ever overwriting a given value.
"""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicLine, AtomicPoint, AtomicVector
from pyhopper.Utils.Planes import plane_coordinates, plane_from_points
from pyhopper.Utils.Vectors import cross, distance, dot, is_zero, midpoint, sub, translate, unit

_TOLERANCE = 1e-9


def _check_triangle(a: AtomicPoint, b: AtomicPoint, c: AtomicPoint, component: str) -> AtomicVector:
    normal = cross(sub(b, a), sub(c, a))
    if is_zero(normal):
        raise ValueError(f"{component} needs three non-collinear points")
    return normal


def centroid_medians(a: AtomicPoint, b: AtomicPoint, c: AtomicPoint) -> tuple[AtomicPoint, AtomicLine, AtomicLine, AtomicLine]:
    """Centroid and the medians running from each edge midpoint to the opposite corner."""
    _check_triangle(a, b, c, "Centroid")
    centroid = AtomicPoint((a.x + b.x + c.x) / 3.0, (a.y + b.y + c.y) / 3.0, (a.z + b.z + c.z) / 3.0)
    return centroid, AtomicLine(midpoint(a, b), c), AtomicLine(midpoint(b, c), a), AtomicLine(midpoint(c, a), b)


def circumcentre(a: AtomicPoint, b: AtomicPoint, c: AtomicPoint) -> AtomicPoint:
    """Circumcentre of the triangle (in its own plane, so it works for 3D triangles)."""
    normal = _check_triangle(a, b, c, "Circumcentre")
    ab, ac = sub(b, a), sub(c, a)
    ab2, ac2 = dot(ab, ab), dot(ac, ac)
    # A + (|AB|² (AC × n) + |AC|² (n × AB)) / (2 |n|²)
    u, v = cross(ac, normal), cross(normal, ab)
    offset = AtomicVector(ab2 * u.x + ac2 * v.x, ab2 * u.y + ac2 * v.y, ab2 * u.z + ac2 * v.z)
    return translate(a, offset, 1.0 / (2.0 * dot(normal, normal)))


def _ray_segment_parameter(origin: AtomicPoint, direction: AtomicVector, start: AtomicPoint, end: AtomicPoint, plane) -> float | None:
    """Ray parameter where ``origin + t·direction`` crosses the coplanar segment ``start-end`` (None if it misses)."""
    ox, oy, _ = plane_coordinates(plane, origin)
    dx, dy, _ = plane_coordinates(plane, translate(origin, direction))
    dx, dy = dx - ox, dy - oy
    sx, sy, _ = plane_coordinates(plane, start)
    ex, ey, _ = plane_coordinates(plane, end)
    ex, ey = ex - sx, ey - sy
    determinant = dx * (-ey) - dy * (-ex)
    if abs(determinant) <= _TOLERANCE:
        return None
    rx, ry = sx - ox, sy - oy
    t = (rx * (-ey) - ry * (-ex)) / determinant
    s = (dx * ry - dy * rx) / determinant
    if t <= _TOLERANCE or s < -_TOLERANCE or s > 1.0 + _TOLERANCE:
        return None
    return t


def circumcentre_bisectors(a: AtomicPoint, b: AtomicPoint, c: AtomicPoint) -> tuple[AtomicPoint, AtomicLine, AtomicLine, AtomicLine]:
    """Circumcentre and Grasshopper's bisector segments: from each edge midpoint, perpendicular to the
    edge into the triangle, up to the first other edge."""
    centre = circumcentre(a, b, c)
    plane = plane_from_points(a, b, c)
    lines = []
    for start, end, opposite, others in ((a, b, c, ((b, c), (c, a))), (b, c, a, ((c, a), (a, b))), (c, a, b, ((a, b), (b, c)))):
        middle = midpoint(start, end)
        direction = unit(cross(plane.normal, sub(end, start)))
        if dot(direction, sub(opposite, middle)) < 0.0:
            direction = AtomicVector(-direction.x, -direction.y, -direction.z)
        hits = [t for t in (_ray_segment_parameter(middle, direction, p, q, plane) for p, q in others) if t is not None]
        lines.append(AtomicLine(middle, translate(middle, direction, min(hits) if hits else 0.0)))
    return centre, lines[0], lines[1], lines[2]


def incentre_bisectors(a: AtomicPoint, b: AtomicPoint, c: AtomicPoint) -> tuple[AtomicPoint, AtomicLine, AtomicLine, AtomicLine]:
    """Incentre and the angle bisectors running from each corner to the opposite edge."""
    _check_triangle(a, b, c, "Incentre")
    la, lb, lc = distance(b, c), distance(c, a), distance(a, b)  # edge lengths opposite A, B, C
    perimeter = la + lb + lc
    centre = AtomicPoint(
        (la * a.x + lb * b.x + lc * c.x) / perimeter,
        (la * a.y + lb * b.y + lc * c.y) / perimeter,
        (la * a.z + lb * b.z + lc * c.z) / perimeter,
    )

    def bisector(corner, start, end, near, far):
        # the bisector meets the opposite edge at the point dividing it in the ratio of the adjacent sides
        return AtomicLine(corner, translate(start, sub(end, start), near / (near + far)))

    return centre, bisector(a, b, c, lc, lb), bisector(b, c, a, la, lc), bisector(c, a, b, lb, la)


def _foot(point: AtomicPoint, start: AtomicPoint, end: AtomicPoint) -> AtomicPoint:
    direction = sub(end, start)
    return translate(start, direction, dot(sub(point, start), direction) / dot(direction, direction))


def orthocentre_altitudes(a: AtomicPoint, b: AtomicPoint, c: AtomicPoint) -> tuple[AtomicPoint, AtomicLine, AtomicLine, AtomicLine]:
    """Orthocentre and the altitudes running from the foot on each (infinite) edge to the opposite corner."""
    _check_triangle(a, b, c, "Orthocentre")
    centre = circumcentre(a, b, c)
    ortho = AtomicPoint(a.x + b.x + c.x - 2.0 * centre.x, a.y + b.y + c.y - 2.0 * centre.y, a.z + b.z + c.z - 2.0 * centre.z)
    return ortho, AtomicLine(_foot(c, a, b), c), AtomicLine(_foot(a, b, c), a), AtomicLine(_foot(b, c, a), b)


def solve_triangle(angles: list[float | None], sides: list[float | None], *, component: str = "Triangle Trigonometry") -> tuple[list[float | None], list[float | None]]:
    """Fill in the unknown angles and sides of a triangle (``sides[i]`` is opposite ``angles[i]``).

    Grasshopper's rules, in priority order and re-scanned after every hit: two known angles give
    the third; three known sides give the missing angles (law of cosines); two sides with their
    included angle give the third side (law of cosines); a side with its opposite angle gives the
    other sides from their angles and, failing that, the other angles from their sides (law of
    sines, acute solution). Given values are
    never overwritten and only given angles are checked against pi (Grasshopper does not re-check
    what it computed); unknowns stay ``None``. Impossible triangles raise ``ValueError``.
    """
    angles = [None if value is None else float(value) for value in angles]
    sides = [None if value is None else float(value) for value in sides]
    labels = ("Alpha", "Beta", "Gamma")
    for label, value in zip(labels, angles):
        if value is not None and not 0.0 < value < math.pi:
            raise ValueError(f"{component}: {label} must lie strictly between 0 and pi")
    for label, value in zip(("A", "B", "C"), sides):
        if value is not None and value <= 0.0:
            raise ValueError(f"{component}: edge {label} length must be positive")

    if all(value is not None for value in angles) and abs(sum(angles) - math.pi) > 1e-6:
        raise ValueError(f"{component}: the angles do not sum to pi")

    def other(index):
        return [k for k in range(3) if k != index]

    def law_of_cosines_angle(k):
        i, j = other(k)
        cosine = (sides[i] ** 2 + sides[j] ** 2 - sides[k] ** 2) / (2.0 * sides[i] * sides[j])
        if cosine < -1.0 - 1e-9 or cosine > 1.0 + 1e-9:
            raise ValueError(f"{component}: one edge is longer than the other two combined")
        return math.acos(max(-1.0, min(1.0, cosine)))

    # Rules in Grasshopper's priority order; every hit restarts the scan.
    while True:
        known_angles = [k for k in range(3) if angles[k] is not None]
        known_sides = [k for k in range(3) if sides[k] is not None]
        if len(known_angles) == 2:
            remainder = math.pi - sum(angles[k] for k in known_angles)
            if remainder <= 0.0:
                raise ValueError(f"{component}: two angles already sum to pi or more")
            angles[3 - sum(known_angles)] = remainder
            continue
        if len(known_sides) == 3 and len(known_angles) < 3:
            for k in range(3):
                if angles[k] is None:
                    angles[k] = law_of_cosines_angle(k)
            continue
        if len(known_sides) == 2:
            k = 3 - sum(known_sides)  # the missing side, opposite the included angle
            if angles[k] is not None:
                i, j = other(k)
                sides[k] = math.sqrt(max(sides[i] ** 2 + sides[j] ** 2 - 2.0 * sides[i] * sides[j] * math.cos(angles[k]), 0.0))
                continue
        pairs = [k for k in range(3) if sides[k] is not None and angles[k] is not None and math.sin(angles[k]) > 1e-12]
        if pairs:
            ratio = sides[pairs[0]] / math.sin(angles[pairs[0]])
            missing_sides = [m for m in range(3) if sides[m] is None and angles[m] is not None]
            if missing_sides:
                for m in missing_sides:
                    sides[m] = ratio * math.sin(angles[m])
                continue
            missing_angles = [m for m in range(3) if angles[m] is None and sides[m] is not None]
            if missing_angles:
                for m in missing_angles:
                    sine = sides[m] / ratio
                    if sine > 1.0 + 1e-9:
                        raise ValueError(f"{component}: no triangle has these sides and angles")
                    angles[m] = math.asin(min(sine, 1.0))
                continue
        break
    return angles, sides
