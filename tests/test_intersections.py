"""Intersection kernel behind the K4 wave (curve|plane, curve|curve, self, curve|line, surface|line,
brep sections, plane regions, contour planes, region trimming).

The expected numbers were read off Grasshopper 8 with the probes recorded while building the wave
(rhino-test/oracle/cases/{Intersect,Curve}/*.json hold the full comparisons).
"""

from __future__ import annotations

import math
import unittest

from pyhopper.Core.Atoms import AtomicArc, AtomicBox, AtomicBrep, AtomicCircle, AtomicLine, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicPolyCurve, AtomicPolyline, AtomicSurface, AtomicVector
from pyhopper.Utils.Intersections import (
    brep_line_intersections,
    brep_plane_section,
    contour_offsets,
    cumulative_offsets,
    curve_curve_intersections,
    curve_line_intersections,
    curve_plane_intersections,
    curve_self_intersections,
    extent_along,
    plane_region,
    surface_line_intersections,
    surface_line_overlaps,
    surface_plane_section,
    trim_with_regions,
)
from pyhopper.Utils.Vectors import distance

P, V = AtomicPoint, AtomicVector


def nurbs(points, degree=3):
    count = len(points)
    knots = [0.0] * (degree + 1) + [i / (count - degree) for i in range(1, count - degree)] + [1.0] * (degree + 1)
    return AtomicNurbsCurve(tuple(P(*p) for p in points), (1.0,) * count, tuple(knots), degree)


def surface(rows, u_degree, v_degree):
    return AtomicSurface(poles=tuple(tuple(P(*p) for p in row) for row in rows), weights=tuple((1.0,) * len(row) for row in rows),
                         u_knots=(0.0, 1.0), v_knots=(0.0, 1.0), u_mults=(u_degree + 1, u_degree + 1), v_mults=(v_degree + 1, v_degree + 1),
                         u_degree=u_degree, v_degree=v_degree)


def plane(origin, normal, x_axis):
    return AtomicPlane(P(*origin), V(*normal), V(*x_axis))


CUBIC = nurbs([(0, 0, 0), (1, 2, 0), (3, 2, 1), (4, 0, 0)])
WAVE = nurbs([(0, 0, 0), (1, 3, 0), (2, -3, 0), (3, 3, 0), (4, 0, 0)])
FIGURE8 = nurbs([(0, 0, 0), (4, 4, 0), (4, 0, 0), (0, 4, 0), (0, 0, 0)])
CIRCLE = AtomicCircle(AtomicPlane.world_xy(), 2.0)
LINE = AtomicLine(P(0, 0, 0), P(4, 0, 0))
PLINE = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(4, 2, 0)))
CLOSED = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(0, 2, 0), P(0, 0, 0)))
ZIGZAG = AtomicPolyline((P(0, 0, 0), P(4, 0, 0), P(4, 2, 0), P(1, 2, 0), P(1, -1, 0), P(3, -1, 0), P(3, 3, 0)))
DOME = surface([[(0, 0, 0), (2, 0, 1), (4, 0, 0)], [(0, 2, 1), (2, 2, 3), (4, 2, 1)], [(0, 4, 0), (2, 4, 1), (4, 4, 0)]], 2, 2)
FLAT = surface([[(0, 0, 0), (4, 0, 0)], [(0, 2, 0), (4, 2, 0)]], 1, 1)
BOX = AtomicBox(plane((2, 2, 1), (0, 0, 1), (1, 0, 0)), 4.0, 4.0, 2.0)
YZ_AT_X1 = plane((1, 0, 0), (1, 0, 0), (0, 1, 0))
XZ = plane((0, 0, 0), (0, 1, 0), (1, 0, 0))
XZ_AT_Y1 = plane((0, 1, 0), (0, 1, 0), (1, 0, 0))


def close(test, actual, expected, places=5):
    for a, e in zip((actual.x, actual.y, actual.z), expected):
        test.assertAlmostEqual(a, e, places=places)


class CurvePlaneTests(unittest.TestCase):
    def test_cubic_matches_grasshopper(self):
        events = curve_plane_intersections(CUBIC, YZ_AT_X1)
        self.assertEqual(len(events), 1)
        self.assertAlmostEqual(events[0][0], 0.2725480, places=6)
        close(self, events[0][1], (1.0, 1.18959, 0.16211))

    def test_wave_crossings_sorted_by_parameter(self):
        params = [t for t, _ in curve_plane_intersections(WAVE, XZ_AT_Y1)]
        for actual, expected in zip(params, (0.0779852, 0.2754506, 0.7245494, 0.9220148)):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_closed_seam_is_one_event_at_the_start(self):
        params = [t for t, _ in curve_plane_intersections(CIRCLE, XZ)]
        self.assertEqual(len(params), 2)
        self.assertAlmostEqual(params[0], 0.0)
        self.assertAlmostEqual(params[1], 0.5)
        corner = curve_plane_intersections(CLOSED, plane((0, 0, 0), (1, 1, 0), (0, 0, 1)))
        self.assertEqual([round(t, 9) for t, _ in corner], [0.0])

    def test_seam_twice_for_contours(self):
        params = [t for t, _ in curve_plane_intersections(CIRCLE, XZ, seam_twice=True)]
        self.assertEqual([round(t, 9) for t in params], [0.0, 0.5, 1.0])

    def test_touch_and_coplanar_stretch(self):
        touch = curve_plane_intersections(CIRCLE, plane((2, 0, 0), (1, 0, 0), (0, 1, 0)))
        self.assertEqual(len(touch), 1)
        close(self, touch[0][1], (2.0, 0.0, 0.0))
        coplanar = curve_plane_intersections(LINE, AtomicPlane.world_xy())
        self.assertEqual([t for t, _ in coplanar], [0.0, 1.0])
        self.assertEqual(curve_plane_intersections(LINE, XZ_AT_Y1), [])

    def test_polyline_vertices_count_once(self):
        events = curve_plane_intersections(PLINE, plane((2, 0, 0), (1, 0, 0), (0, 1, 0)))
        self.assertEqual([round(t * 3, 9) for t, _ in events], [1.0, 2.0])


class CurveCurveTests(unittest.TestCase):
    def test_wave_and_line(self):
        events = curve_curve_intersections(WAVE, AtomicLine(P(0, 1, 0), P(4, 1, 0)))
        self.assertEqual(len(events), 4)
        for (ta, tb, point), x in zip(events, (0.43332, 1.28106, 2.71894, 3.56668)):
            self.assertAlmostEqual(point.x, x, places=4)
            self.assertAlmostEqual(tb * 4, x, places=4)

    def test_point_is_the_midpoint_within_tolerance(self):
        events = curve_curve_intersections(LINE, AtomicLine(P(2, -1, 0.005), P(2, 1, 0.005)))
        self.assertEqual(len(events), 1)
        close(self, events[0][2], (2.0, 0.0, 0.0025))
        self.assertEqual(curve_curve_intersections(LINE, AtomicLine(P(2, -1, 0.1), P(2, 1, 0.1))), [])

    def test_collinear_overlap_reports_both_ends(self):
        events = curve_curve_intersections(LINE, AtomicLine(P(2, 0, 0), P(6, 0, 0)))
        self.assertEqual([(round(a * 4, 9), round(b * 4, 9)) for a, b, _ in events], [(2.0, 0.0), (4.0, 2.0)])

    def test_tangent_at_the_seam_counts_once(self):
        events = curve_curve_intersections(CIRCLE, AtomicLine(P(2, -1, 0), P(2, 1, 0)))
        self.assertEqual(len(events), 1)
        self.assertAlmostEqual(events[0][0], 0.0)
        self.assertAlmostEqual(events[0][1], 0.5)

    def test_polylines(self):
        events = curve_curve_intersections(PLINE, AtomicPolyline((P(-1, 1, 0), P(3, 1, 0), P(3, 3, 0))))
        self.assertEqual([(round(a * 3, 6), round(b * 2, 6)) for a, b, _ in events], [(1.5, 0.75), (2.5, 1.5)])


class CurveSelfTests(unittest.TestCase):
    def test_figure_eight(self):
        events = curve_self_intersections(FIGURE8)
        self.assertEqual(len(events), 1)
        self.assertAlmostEqual(events[0][0], 0.1388277, places=6)
        self.assertAlmostEqual(events[0][1], 0.5779208, places=6)
        close(self, events[0][2], (2.47097, 2.11544, 0.0), places=4)

    def test_three_crossings_sorted_by_first_parameter(self):
        events = curve_self_intersections(ZIGZAG)
        self.assertEqual([(round(a * 6, 6), round(b * 6, 6)) for a, b, _ in events], [(0.25, 3.666667), (0.75, 5.25), (2.333333, 5.75)])

    def test_no_events(self):
        self.assertEqual(curve_self_intersections(CUBIC), [])
        self.assertEqual(curve_self_intersections(CIRCLE), [])


class CurveLineTests(unittest.TestCase):
    def test_line_is_infinite(self):
        short = curve_line_intersections(CIRCLE, AtomicLine(P(0, 0.5, 0), P(1, 0.5, 0)))
        self.assertEqual(len(short), 2)
        close(self, short[0][1], (1.93649, 0.5, 0.0))
        close(self, short[1][1], (-1.93649, 0.5, 0.0))

    def test_skew_within_tolerance_returns_the_curve_point(self):
        events = curve_line_intersections(LINE, AtomicLine(P(2, -1, 0.005), P(2, 1, 0.005)))
        self.assertEqual(len(events), 1)
        close(self, events[0][1], (2.0, 0.0, 0.0))

    def test_zero_length_line_raises(self):
        with self.assertRaises(ValueError):
            curve_line_intersections(CIRCLE, AtomicLine(P(1, 1, 0), P(1, 1, 0)))


class SurfaceLineTests(unittest.TestCase):
    def test_dome_hit_with_uv_and_normal(self):
        hits = surface_line_intersections(DOME, AtomicLine(P(1, 1, 5), P(1, 1, 0)))
        self.assertEqual(len(hits), 1)
        u, v, point, normal, _ = hits[0]
        self.assertAlmostEqual(u, 0.25)
        self.assertAlmostEqual(v, 0.25)
        close(self, point, (1.0, 1.0, 0.890625))
        close(self, normal, (-0.30915, -0.30915, 0.89936))

    def test_hits_on_the_boundary_are_kept(self):
        hits = surface_line_intersections(DOME, AtomicLine(P(0, 2, 0.5), P(4, 2, 0.5)))
        self.assertEqual([(round(u, 9), round(v, 9)) for u, v, _, _, _ in hits], [(0.0, 0.5), (1.0, 0.5)])
        self.assertEqual(surface_line_intersections(DOME, AtomicLine(P(0, 2, 0.4), P(4, 2, 0.4))), [])

    def test_planar_overlap_is_clipped_to_the_face(self):
        overlaps = surface_line_overlaps(FLAT, AtomicLine(P(-1, 1, 0), P(1, 1, 0)))
        self.assertEqual(len(overlaps), 1)
        close(self, overlaps[0].start, (0.0, 1.0, 0.0))
        close(self, overlaps[0].end, (4.0, 1.0, 0.0))
        self.assertEqual(surface_line_overlaps(FLAT, AtomicLine(P(1, 3, 0), P(3, 3, 0))), [])
        self.assertEqual(surface_line_overlaps(DOME, AtomicLine(P(1, 1, 0), P(3, 1, 0))), [])


class BrepLineTests(unittest.TestCase):
    def test_points_follow_rhino_face_order(self):
        overlaps, points = brep_line_intersections(BOX, AtomicLine(P(-1, 2, 1), P(5, 2, 1)))
        self.assertEqual(overlaps, [])
        self.assertEqual([(p.x, p.y, p.z) for p in points], [(4.0, 2.0, 1.0), (0.0, 2.0, 1.0)])
        _, vertical = brep_line_intersections(BOX, AtomicLine(P(2, 2, -1), P(2, 2, 5)))
        self.assertEqual([p.z for p in vertical], [0.0, 2.0])

    def test_edge_hits_count_once(self):
        _, points = brep_line_intersections(BOX, AtomicLine(P(-1, -1, 1), P(5, 5, 1)))
        self.assertEqual([(p.x, p.y, p.z) for p in points], [(0.0, 0.0, 1.0), (4.0, 4.0, 1.0)])

    def test_overlap_suppresses_its_end_points(self):
        overlaps, points = brep_line_intersections(BOX, AtomicLine(P(1, 1, 2), P(3, 1, 2)))
        self.assertEqual(len(overlaps), 1)
        close(self, overlaps[0].start, (0.0, 1.0, 2.0))
        close(self, overlaps[0].end, (4.0, 1.0, 2.0))
        self.assertEqual(points, [])
        along_edge, edge_points = brep_line_intersections(BOX, AtomicLine(P(0, 0, -1), P(0, 0, 5)))
        self.assertEqual(len(along_edge), 1)
        self.assertEqual(edge_points, [])


class SectionTests(unittest.TestCase):
    def test_box_section_is_one_closed_polyline(self):
        curves = brep_plane_section(BOX, plane((0, 0, 1), (0, 0, 1), (1, 0, 0)))
        self.assertEqual(len(curves), 1)
        self.assertIsInstance(curves[0], AtomicPolyline)
        self.assertEqual(len(curves[0].points), 5)
        self.assertTrue(all(p.z == 1.0 for p in curves[0].points))

    def test_coplanar_face_is_reported_once(self):
        curves = brep_plane_section(BOX, plane((0, 0, 2), (0, 0, 1), (1, 0, 0)))
        self.assertEqual(len(curves), 1)
        self.assertEqual(sorted((p.x, p.y) for p in curves[0].points[:-1]), [(0.0, 0.0), (0.0, 4.0), (4.0, 0.0), (4.0, 4.0)])

    def test_dome_sections(self):
        closed = brep_plane_section(AtomicBrep((DOME,)), plane((0, 0, 1), (0, 0, 1), (1, 0, 0)))
        self.assertEqual(len(closed), 1)
        self.assertIsInstance(closed[0], AtomicNurbsCurve)
        open_section = surface_plane_section(DOME, YZ_AT_X1)
        self.assertEqual(len(open_section), 1)
        self.assertEqual(brep_plane_section(AtomicBrep((DOME,)), plane((0, 0, 10), (0, 0, 1), (1, 0, 0))), [])

    def test_flat_surface_section_is_a_line(self):
        curves = brep_plane_section(FLAT, XZ_AT_Y1)
        self.assertEqual(len(curves), 1)
        self.assertIsInstance(curves[0], AtomicLine)

    def test_other_geometry_raises(self):
        with self.assertRaises(TypeError):
            brep_plane_section(CIRCLE, XZ)


class PlaneRegionTests(unittest.TestCase):
    BOUNDS = [plane((0, 0, 0), (-1, 0, 0), (0, 1, 0)), plane((4, 0, 0), (1, 0, 0), (0, 1, 0)), plane((0, 0, 0), (0, -1, 0), (1, 0, 0)), plane((0, 3, 0), (0, 1, 0), (1, 0, 0))]

    def test_bounds_through_the_origin_are_ignored(self):
        region = plane_region(AtomicPlane.world_xy(), self.BOUNDS)
        self.assertEqual([(p.x, p.y) for p in region.points], [(-10.0, -10.0), (4.0, -10.0), (4.0, 3.0), (-10.0, 3.0), (-10.0, -10.0)])

    def test_cell_around_an_offset_origin(self):
        region = plane_region(plane((1, 1, 0), (0, 0, 1), (1, 0, 0)), self.BOUNDS)
        self.assertEqual(sorted((p.x, p.y) for p in region.points[:-1]), [(0.0, 0.0), (0.0, 3.0), (4.0, 0.0), (4.0, 3.0)])

    def test_triangle(self):
        region = plane_region(AtomicPlane.world_xy(), [plane((0, -1, 0), (0, 1, 0), (1, 0, 0)), plane((3, 0, 0), (1, 1, 0), (0, 0, 1)), plane((-3, 0, 0), (-1, 1, 0), (0, 0, 1))])
        self.assertEqual(sorted((round(p.x, 9), round(p.y, 9)) for p in region.points[:-1]), [(-4.0, -1.0), (0.0, 3.0), (4.0, -1.0)])

    def test_too_few_bounds_raise(self):
        with self.assertRaises(ValueError):
            plane_region(AtomicPlane.world_xy(), self.BOUNDS[:1])
        with self.assertRaises(ValueError):
            plane_region(AtomicPlane.world_xy(), [self.BOUNDS[1], self.BOUNDS[0]])


class ContourTests(unittest.TestCase):
    def test_offsets_cover_the_extent_from_the_start(self):
        self.assertEqual(contour_offsets((0.0, 4.0), 0.0, 1.0), [0.0, 1.0, 2.0, 3.0])
        self.assertEqual(contour_offsets((-1.5, 2.5), 0.0, 1.0), [-1.0, 0.0, 1.0, 2.0])
        self.assertEqual(contour_offsets((0.0, 4.0), 0.0, 1.5), [0.0, 1.5, 3.0])
        with self.assertRaises(ValueError):
            contour_offsets((0.0, 4.0), 0.0, 0.0)

    def test_extent_hugs_the_geometry(self):
        low, high = extent_along(WAVE, P(0, 0, 0), V(0, 1, 0))
        self.assertAlmostEqual(low, 0.0, places=6)
        self.assertAlmostEqual(high, 4.0 / 3.0, places=3)  # the curve's own crest, not its control point at y = 3
        self.assertEqual(extent_along(BOX, P(0, 0, 0), V(0, 0, 1)), (0.0, 2.0))
        low, high = extent_along(AtomicBrep((DOME,)), P(0, 0, 0), V(0, 0, 1))
        self.assertAlmostEqual(low, 0.0, places=6)
        self.assertAlmostEqual(high, 1.25, places=4)

    def test_cumulative_offsets(self):
        self.assertEqual(cumulative_offsets([1.5, 0.5], [1.0]), [1.5, 0.5])
        self.assertEqual(cumulative_offsets(None, [0.5, 1.0, 1.0]), [0.5, 1.5, 2.5])
        with self.assertRaises(ValueError):
            cumulative_offsets([], [])


class TrimTests(unittest.TestCase):
    def test_pieces_are_classified_by_their_midpoint(self):
        inside, outside = trim_with_regions(AtomicLine(P(-1, 1, 0), P(5, 1, 0)), [CIRCLE], None)
        self.assertEqual(len(inside), 1)
        self.assertEqual(len(outside), 1)
        close(self, inside[0].end, (math.sqrt(3), 1.0, 0.0))
        close(self, outside[0].start, (math.sqrt(3), 1.0, 0.0))

    def test_projection_onto_the_region_plane(self):
        inside, outside = trim_with_regions(AtomicLine(P(-1, 1, 1), P(5, 1, 1)), [CIRCLE], None)
        self.assertEqual((len(inside), len(outside)), (1, 1))
        self.assertEqual(inside[0].start.z, 1.0)

    def test_touching_splits_without_an_inside(self):
        inside, outside = trim_with_regions(AtomicLine(P(-1, 2, 0), P(5, 2, 0)), [CIRCLE], None)
        self.assertEqual(inside, [])
        self.assertEqual(len(outside), 2)
        close(self, outside[0].end, (0.0, 2.0, 0.0))

    def test_closed_curve_keeps_the_seam_in_a_polycurve(self):
        inside, outside = trim_with_regions(AtomicCircle(plane((2, 0, 0), (0, 0, 1), (1, 0, 0)), 2.0), [CIRCLE], None)
        self.assertEqual(len(inside), 1)
        self.assertIsInstance(inside[0], AtomicArc)
        self.assertEqual(len(outside), 1)
        self.assertIsInstance(outside[0], AtomicPolyCurve)
        self.assertEqual(len(outside[0].segments), 2)

    def test_several_regions_and_open_regions(self):
        square = CLOSED
        inside, outside = trim_with_regions(AtomicLine(P(-1, 1, 0), P(5, 1, 0)), [CIRCLE, square], None)
        self.assertEqual([round(piece.end.x, 5) for piece in inside], [0.0, round(math.sqrt(3), 5), 2.0])
        self.assertEqual([round(piece.end.x, 5) for piece in outside], [5.0])
        with self.assertRaises(ValueError):
            trim_with_regions(LINE, [WAVE], None)

    def test_untouched_curves(self):
        inside, outside = trim_with_regions(AtomicLine(P(-0.5, 0, 0), P(0.5, 0, 0)), [CIRCLE], None)
        self.assertEqual((len(inside), len(outside)), (1, 0))
        inside, outside = trim_with_regions(AtomicLine(P(5, 0, 0), P(6, 0, 0)), [CIRCLE], None)
        self.assertEqual((len(inside), len(outside)), (0, 1))
        self.assertLess(distance(outside[0].start, P(5, 0, 0)), 1e-12)


if __name__ == "__main__":
    unittest.main()
