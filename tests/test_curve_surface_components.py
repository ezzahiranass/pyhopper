import math
import unittest

from pyhopper import Extrude, OffsetCurve, Polygon, RuledSurface
from pyhopper.Core.Atoms import (
    AtomicBrep,
    AtomicCircle,
    AtomicLine,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicSurface,
    AtomicVector,
)


class CurveSurfaceComponentTests(unittest.TestCase):
    def setUp(self):
        self.plane = AtomicPlane.world_xy()
        self.square = AtomicPolyline(
            (
                AtomicPoint(0.0, 0.0, 0.0),
                AtomicPoint(10.0, 0.0, 0.0),
                AtomicPoint(10.0, 10.0, 0.0),
                AtomicPoint(0.0, 10.0, 0.0),
                AtomicPoint(0.0, 0.0, 0.0),
            )
        )

    def test_polygon_fillet_changes_geometry_and_length(self):
        plain = Polygon(self.plane, 10.0, 6, 0.0)
        rounded = Polygon(self.plane, 10.0, 6, 2.0)

        self.assertGreater(len(rounded.all_items()[0].points), len(plain.all_items()[0].points))
        self.assertLess(rounded.length.all_items()[0], plain.length.all_items()[0])

    def test_offset_curve_corner_styles(self):
        for corners in range(5):
            with self.subTest(corners=corners):
                items = OffsetCurve(self.square, 1.0, self.plane, corners).all_items()
                self.assertEqual(len(items), 4 if corners == 0 else 1)

        circle = OffsetCurve(AtomicCircle(self.plane, 5.0), 1.0, self.plane, 2).all_items()[0]
        self.assertTrue(math.isclose(circle.radius, 4.0))

    def test_ruled_surface_and_extrude_types(self):
        line_a = AtomicLine(AtomicPoint(0.0, 0.0, 0.0), AtomicPoint(10.0, 0.0, 0.0))
        line_b = AtomicLine(AtomicPoint(0.0, 0.0, 5.0), AtomicPoint(10.0, 0.0, 5.0))
        ruled = RuledSurface(line_a, line_b).all_items()[0]
        curve_extrusion = Extrude(self.square, AtomicVector(0.0, 0.0, 5.0)).all_items()[0]
        solid_extrusion = Extrude(ruled, AtomicVector(0.0, 5.0, 0.0)).all_items()[0]

        self.assertIsInstance(ruled, AtomicSurface)
        self.assertIsInstance(curve_extrusion, AtomicSurface)
        self.assertIsInstance(solid_extrusion, AtomicBrep)
        self.assertEqual(solid_extrusion.face_count, 6)


if __name__ == "__main__":
    unittest.main()
