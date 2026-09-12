"""Wave A4 helpers: point sorting/proximity/duplicates, plane construction, best-candidate sampling."""

from __future__ import annotations

import math
import unittest

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicRectangle, AtomicVector
from pyhopper.Utils.Planes import align_plane, plane_from_points
from pyhopper.Utils.Points import average_point, group_coincident, nearest_indices, sort_points
from pyhopper.Utils.Sampling import min_spacing, populate_rectangle

P = AtomicPoint
V = AtomicVector


class PointHelperTests(unittest.TestCase):
    def test_sort_points_is_lexicographic_and_stable(self):
        points = [P(1, 0, 0), P(0, 5, 0), P(0, 0, 3), P(0, 0, 1), P(0, 0, 1)]
        ordered, indices = sort_points(points)
        self.assertEqual(indices, [3, 4, 2, 1, 0])
        self.assertEqual(ordered[0], P(0, 0, 1))

    def test_nearest_indices_orders_by_distance_then_index(self):
        cloud = [P(1, 0, 0), P(0, 2, 0), P(-1, 0, 0)]
        self.assertEqual(nearest_indices(P(0, 0, 0), cloud), [(0, 1.0), (2, 1.0), (1, 2.0)])
        self.assertEqual(nearest_indices(P(0, 0, 0), cloud, 1), [(0, 1.0)])
        self.assertEqual(nearest_indices(P(0, 0, 0), cloud, 9), nearest_indices(P(0, 0, 0), cloud))
        self.assertEqual(nearest_indices(P(0, 0, 0), [], 3), [])

    def test_group_coincident_is_greedy_against_the_group_seed(self):
        points = [P(0, 0, 0), P(0.0008, 0, 0), P(0.0016, 0, 0)]
        self.assertEqual(group_coincident(points, 0.001), [[0, 1], [2]])
        self.assertEqual(average_point([P(0, 0, 0), P(0.0008, 0, 0)]), P(0.0004, 0, 0))


class PlaneHelperTests(unittest.TestCase):
    def test_plane_from_points_orientation(self):
        plane = plane_from_points(P(0, 0, 0), P(2, 0, 0), P(1, -3, 0))
        self.assertEqual(plane.normal, V(0.0, 0.0, -1.0))
        self.assertEqual(plane.x_axis, V(1.0, 0.0, 0.0))
        with self.assertRaises(ValueError):
            plane_from_points(P(0, 0, 0), P(1, 0, 0), P(2, 0, 0))

    def test_align_plane_signed_angle(self):
        aligned, angle = align_plane(AtomicPlane.world_xy(), V(0, -1, 0))
        self.assertAlmostEqual(angle, -math.pi / 2)
        self.assertEqual(aligned.x_axis, V(0.0, -1.0, 0.0))
        with self.assertRaises(ValueError):
            align_plane(AtomicPlane.world_xy(), V(0, 0, 1))


class SamplingTests(unittest.TestCase):
    def setUp(self):
        self.region = AtomicRectangle(AtomicPlane.world_xy(P(5, 5, 0)), 10.0, 10.0)

    def test_points_stay_inside_and_are_deterministic(self):
        first = populate_rectangle(self.region, 30, seed=7)
        second = populate_rectangle(self.region, 30, seed=7)
        self.assertEqual(first, second)
        for point in first:
            self.assertTrue(0.0 <= point.x <= 10.0 and 0.0 <= point.y <= 10.0 and point.z == 0.0)
        self.assertNotEqual(first, populate_rectangle(self.region, 30, seed=8))

    def test_best_candidate_spreads_points_out(self):
        # 30 well-spread points in a 10x10 square keep a spacing a plain random scatter rarely reaches
        spread = populate_rectangle(self.region, 30, seed=3)
        self.assertGreater(min_spacing(spread), 0.6)

    def test_seed_points_repel_but_are_not_emitted(self):
        anchor = P(5, 5, 0)
        population = populate_rectangle(self.region, 12, seed=1, existing=[anchor])
        self.assertEqual(len(population), 12)
        self.assertNotIn(anchor, population)
        self.assertGreater(min(math.dist((p.x, p.y), (5, 5)) for p in population), 0.5)


if __name__ == "__main__":
    unittest.main()
