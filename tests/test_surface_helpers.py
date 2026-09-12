"""Wave A6 helpers: bounds, boxes, closed-form intersections, surface builders (numbers from the Grasshopper probes)."""

from __future__ import annotations

import math
import unittest

from pyhopper.Components.Intersect.Mathematical._closed_form import line_line_closest_points, line_plane_intersection, plane_plane_intersection
from pyhopper.Core.Atoms import AtomicArc, AtomicBox, AtomicCircle, AtomicInterval, AtomicLine, AtomicPlane, AtomicPoint, AtomicSurface, AtomicVector
from pyhopper.Utils.Bounds import bounding_boxes, geometry_extents, minimum_signed_distance
from pyhopper.Utils.Boxes import box_corners, box_from_corners, box_intervals
from pyhopper.Utils.SurfaceBuilders import surface_dimensions, sum_surface
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

P = AtomicPoint
V = AtomicVector
TILTED = AtomicPlane(P(0, 0, 0), V(0, 1, 0), V(1, 0, 0))


class BoundsTests(unittest.TestCase):
    def test_arc_extents_use_the_analytic_extrema(self):
        (x0, x1), (y0, y1), (z0, z1) = geometry_extents(AtomicArc(AtomicPlane.world_xy(), 2.0, AtomicInterval(0.0, math.pi / 2)), AtomicPlane.world_xy())
        self.assertAlmostEqual(x0, 0.0)
        self.assertAlmostEqual(x1, 2.0)
        self.assertAlmostEqual(y1, 2.0)
        self.assertEqual((z0, z1), (0.0, 0.0))

    def test_circle_box_follows_the_plane(self):
        world, local = bounding_boxes([AtomicCircle(AtomicPlane.world_xy(), 2.0)], TILTED)
        self.assertEqual((world[0].x_size, world[0].y_size, world[0].z_size), (4.0, 0.0, 4.0))
        self.assertEqual(world[0].plane.normal, TILTED.normal)
        self.assertEqual(local[0].plane.normal, AtomicVector(0.0, 0.0, 1.0))

    def test_union_and_signed_distance(self):
        world, _ = bounding_boxes([P(0, 0, 0), P(2, 3, 4)], AtomicPlane.world_xy(), union=True)
        self.assertEqual(len(world), 1)
        self.assertEqual((world[0].x_size, world[0].y_size, world[0].z_size), (2.0, 3.0, 4.0))
        self.assertEqual(minimum_signed_distance(AtomicLine(P(0, 0, -1), P(0, 0, 3)), AtomicPlane.world_xy()), -1.0)


class BoxTests(unittest.TestCase):
    def test_corners_from_two_points_in_a_tilted_plane(self):
        box = box_from_corners(TILTED, P(0, 0, 0), P(2, 3, 4))
        self.assertEqual((box.x_size, box.y_size, box.z_size), (2.0, 4.0, 3.0))
        self.assertEqual(box.plane.origin, P(1.0, 1.5, 2.0))
        self.assertEqual(len(box_corners(box)), 8)
        self.assertEqual(box_intervals(AtomicBox(AtomicPlane.world_xy(), 2.0, 3.0, 4.0))[1], AtomicInterval(-1.5, 1.5))


class IntersectionTests(unittest.TestCase):
    def test_line_line_skew_and_parallel(self):
        t_a, t_b, point_a, point_b = line_line_closest_points(AtomicLine(P(0, 0, 0), P(4, 0, 0)), AtomicLine(P(1, -1, 1), P(1, 3, 1)))
        self.assertEqual((t_a, t_b), (0.25, 0.25))
        self.assertEqual((point_a, point_b), (P(1.0, 0.0, 0.0), P(1.0, 0.0, 1.0)))
        self.assertIsNone(line_line_closest_points(AtomicLine(P(0, 0, 0), P(4, 0, 0)), AtomicLine(P(0, 1, 0), P(4, 1, 0))))

    def test_line_plane_reports_plane_coordinates(self):
        point, t, uv = line_plane_intersection(AtomicLine(P(0, 0, -1), P(0, 0, 3)), AtomicPlane.world_xy(P(1, 2, 0)))
        self.assertEqual((point, t, uv), (P(0.0, 0.0, 0.0), 0.25, P(-1.0, -2.0, 0.0)))
        self.assertIsNone(line_plane_intersection(AtomicLine(P(0, 0, 1), P(4, 0, 1)), AtomicPlane.world_xy()))

    def test_plane_plane_grasshopper_line(self):
        line = plane_plane_intersection(AtomicPlane.world_xy(P(0, 0, 1)), AtomicPlane(P(2, 5, 0), V(1, 0, 0), V(0, 1, 0)))
        self.assertEqual(line.start, P(2.0, 2.5, 1.0))
        self.assertEqual(line.end, P(2.0, 1.5, 1.0))
        self.assertIsNone(plane_plane_intersection(AtomicPlane.world_xy(), AtomicPlane.world_xy(P(0, 0, 1))))


class SurfaceBuilderTests(unittest.TestCase):
    def test_dimensions_take_the_longest_control_polygons(self):
        surface = AtomicSurface(poles=((P(0, 0, 0), P(3, 0, 0), P(6, 0, 0)), (P(0, 1, 0), P(3, 1, 4), P(6, 1, 0))), u_degree=2, v_degree=1)
        u, v = surface_dimensions(surface)
        self.assertAlmostEqual(u, 10.0)
        self.assertAlmostEqual(v, math.sqrt(17))

    def test_sum_surface_pins_the_second_curve_start(self):
        surface = sum_surface(as_nurbs_curve(AtomicLine(P(0, 0, 0), P(4, 0, 0))), as_nurbs_curve(AtomicLine(P(1, 1, 0), P(1, 1, 3))))
        self.assertEqual(surface.poles[1][1], P(4.0, 0.0, 3.0))


if __name__ == "__main__":
    unittest.main()
