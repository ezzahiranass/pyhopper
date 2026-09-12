"""Seeded point sampling for the Populate components.

Grasshopper's Populate components scatter points so that they are spread out
rather than uniformly random. pyhopper uses Mitchell's best-candidate
algorithm: every new point is the best of ``candidates`` random draws, "best"
meaning farthest from every point placed so far (including seed points, which
repel but are not emitted). The sequence is deterministic per seed but differs
from Grasshopper's.
"""

from __future__ import annotations

import random
from typing import Iterable, Sequence

from pyhopper.Core.Atoms import AtomicPoint, AtomicRectangle
from pyhopper.Utils.Planes import point_on_plane
from pyhopper.Utils.Vectors import distance

CANDIDATES_PER_POINT = 12


def populate_rectangle(region: AtomicRectangle, count: int, seed: int, existing: Iterable[AtomicPoint] = ()) -> list[AtomicPoint]:
    """``count`` well-spread points inside ``region`` (its plane, centred sizes)."""
    if count < 0:
        raise ValueError("Populate count must not be negative")
    generator = random.Random(int(seed))
    half_x, half_y = float(region.x_size) / 2.0, float(region.y_size) / 2.0

    def draw() -> AtomicPoint:
        return point_on_plane(region.plane, generator.uniform(-half_x, half_x), generator.uniform(-half_y, half_y))

    return best_candidates(draw, count, existing, generator)


def best_candidates(draw, count: int, existing: Iterable[AtomicPoint], generator: random.Random) -> list[AtomicPoint]:
    """Mitchell's best-candidate sampling over an arbitrary ``draw()`` of random points."""
    placed: list[AtomicPoint] = list(existing)
    result: list[AtomicPoint] = []
    for _ in range(count):
        if not placed:
            chosen = draw()
        else:
            chosen = None
            best_gap = -1.0
            for _ in range(CANDIDATES_PER_POINT):
                candidate = draw()
                gap = min(distance(candidate, other) for other in placed)
                if gap > best_gap:
                    best_gap, chosen = gap, candidate
        placed.append(chosen)
        result.append(chosen)
    return result


def min_spacing(points: Sequence[AtomicPoint]) -> float:
    """Smallest pairwise distance (``inf`` for fewer than two points); handy for tests."""
    best = float("inf")
    for index, point in enumerate(points):
        for other in points[index + 1 :]:
            best = min(best, distance(point, other))
    return best
