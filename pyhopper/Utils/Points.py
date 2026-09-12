"""Point-set helpers shared by the Vector components (sorting, proximity, duplicates).

The rules mirror Grasshopper's Point components, checked with the headless
oracle: lexicographic sorting is stable, proximity ties go to the lowest index,
and coincident points are grouped greedily against the first point of a group
and replaced by their average (Grasshopper's default "Average" culling mode).
"""

from __future__ import annotations

from typing import Sequence

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Utils.Vectors import distance


def sort_points(points: Sequence[AtomicPoint]) -> tuple[list[AtomicPoint], list[int]]:
    """Sort by x, then y, then z (stable); also return each point's original index."""
    order = sorted(range(len(points)), key=lambda index: (points[index].x, points[index].y, points[index].z))
    return [points[index] for index in order], order


def nearest_indices(point: AtomicPoint, cloud: Sequence[AtomicPoint], count: int | None = None) -> list[tuple[int, float]]:
    """``(index, distance)`` pairs of the ``count`` nearest cloud points, nearest first.

    Ties keep the lower index first; ``count=None`` (or a count beyond the cloud
    size) returns the whole cloud in proximity order.
    """
    ranked = sorted(((distance(point, candidate), index) for index, candidate in enumerate(cloud)), key=lambda pair: (pair[0], pair[1]))
    if count is not None:
        ranked = ranked[: max(0, count)]
    return [(index, gap) for gap, index in ranked]


def group_coincident(points: Sequence[AtomicPoint], tolerance: float) -> list[list[int]]:
    """Group point indices that lie within ``tolerance`` of the first point of a group.

    Greedy in list order (Grasshopper Cull Duplicates): a point joins the first
    existing group whose seed is close enough, otherwise it starts a new group.
    """
    groups: list[list[int]] = []
    for index, point in enumerate(points):
        for group in groups:
            if distance(points[group[0]], point) <= tolerance:
                group.append(index)
                break
        else:
            groups.append([index])
    return groups


def average_point(points: Sequence[AtomicPoint]) -> AtomicPoint:
    count = len(points)
    return AtomicPoint(sum(p.x for p in points) / count, sum(p.y for p in points) / count, sum(p.z for p in points) / count)


def group_by_distance(points: Sequence[AtomicPoint], distance_limit: float) -> list[list[int]]:
    """Point-index groups linked by chains of points at most ``distance_limit`` apart.

    Grasshopper's Point Groups order: groups appear in order of their highest
    index, members from the highest index down (it walks the list backwards).
    """
    parent = list(range(len(points)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for first in range(len(points)):
        for second in range(first + 1, len(points)):
            if distance(points[first], points[second]) <= distance_limit:
                parent[find(second)] = find(first)
    groups: dict[int, list[int]] = {}
    for index in range(len(points) - 1, -1, -1):
        groups.setdefault(find(index), []).append(index)
    return list(groups.values())


COORDINATE_INDICES = {"x": 0, "y": 1, "z": 2}


def coordinate_mask(mask: str) -> list[int]:
    """Coordinate indices named by a Grasshopper mask such as ``"XYZ"``, ``"xz"`` or ``"ZYX"``."""
    letters = str(mask).strip()
    if not letters or any(letter.lower() not in COORDINATE_INDICES for letter in letters):
        raise ValueError(f"Coordinate mask {mask!r} must use only the letters X, Y and Z")
    return [COORDINATE_INDICES[letter.lower()] for letter in letters]
