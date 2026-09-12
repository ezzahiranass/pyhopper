"""Point-cloud geometry: planar convex hulls, nearest-neighbour proximity links, exact spheres.

Pure Python; the conventions (hull start point and winding, neighbour ordering)
were read off Grasshopper 8 and are recorded on each function.
"""

from __future__ import annotations

import math
from typing import Sequence

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Utils.Nurbs import solve_linear_system
from pyhopper.Utils.Planes import plane_xy
from pyhopper.Utils.Vectors import distance


def convex_hull_indices(points: Sequence[AtomicPoint], plane: AtomicPlane) -> list[int]:
    """Indices of the planar convex hull of ``points`` projected onto ``plane``.

    Andrew's monotone chain; the loop starts at the hull point with the largest
    plane x (smallest plane y among ties) and runs counter-clockwise, collinear
    edge points are dropped — the order Grasshopper's Convex Hull reports.
    """
    flat = [plane_xy(plane, point) for point in points]
    order = sorted(range(len(points)), key=lambda index: (flat[index][0], flat[index][1]))

    def turn(o: int, a: int, b: int) -> float:
        (ox, oy), (ax, ay), (bx, by) = flat[o], flat[a], flat[b]
        return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)

    if len(order) < 3:
        return list(order)
    lower: list[int] = []
    for index in order:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], index) <= 1e-12:
            lower.pop()
        lower.append(index)
    upper: list[int] = []
    for index in reversed(order):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], index) <= 1e-12:
            upper.pop()
        upper.append(index)
    hull = lower[:-1] + upper[:-1]  # counter-clockwise, starting at the lowest-x point
    if len(hull) < 3:
        return hull
    start = max(range(len(hull)), key=lambda position: (flat[hull[position]][0], -flat[hull[position]][1]))
    return hull[start:] + hull[:start]


def proximity_links(points: Sequence[AtomicPoint], group: int, min_radius: float | None, max_radius: float | None, plane: AtomicPlane | None = None) -> list[list[int]]:
    """For every point the indices of its ``group`` nearest other points within the radius range.

    Distances are measured in ``plane`` when one is given (Proximity 2D) and in
    space otherwise; neighbours come closest first, equal distances higher index
    first (Grasshopper's order).
    """
    if plane is not None:
        flat = [plane_xy(plane, point) for point in points]

        def gap(a: int, b: int) -> float:
            return math.hypot(flat[a][0] - flat[b][0], flat[a][1] - flat[b][1])
    else:
        def gap(a: int, b: int) -> float:
            return distance(points[a], points[b])

    links = []
    for index in range(len(points)):
        candidates = []
        for other in range(len(points)):
            if other == index:
                continue
            d = gap(index, other)
            if min_radius is not None and d < min_radius:
                continue
            if max_radius is not None and d > max_radius:
                continue
            candidates.append((d, -other, other))
        candidates.sort()
        links.append([other for _, _, other in candidates[: max(int(group), 0)]])
    return links


def sphere_through_points(a: AtomicPoint, b: AtomicPoint, c: AtomicPoint, d: AtomicPoint) -> tuple[AtomicPoint, float] | None:
    """Centre and radius of the sphere through four points; ``None`` when they are coplanar."""
    rows, rhs = [], []
    for p in (b, c, d):
        rows.append([2.0 * (p.x - a.x), 2.0 * (p.y - a.y), 2.0 * (p.z - a.z)])
        rhs.append([p.x * p.x + p.y * p.y + p.z * p.z - (a.x * a.x + a.y * a.y + a.z * a.z)])
    determinant = (
        rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
        - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
        + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0])
    )
    scale = max(abs(value) for row in rows for value in row) or 1.0
    if abs(determinant) < 1e-12 * scale ** 3:
        return None
    (cx,), (cy,), (cz,) = solve_linear_system(rows, rhs, "coplanar points")
    centre = AtomicPoint(cx, cy, cz)
    return centre, distance(centre, a)
