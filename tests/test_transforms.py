"""AtomicTransform algebra: composition, inverse, and the new factories."""

from __future__ import annotations

import math
import unittest

from pyhopper.Core.Atoms import AtomicCircle, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicTransform, AtomicVector
from pyhopper.Utils.Transforms import apply_transform

P = AtomicPoint
V = AtomicVector


def close(testcase, a, b, places=9):
    for axis in "xyz":
        testcase.assertAlmostEqual(getattr(a, axis), getattr(b, axis), places=places)


class AlgebraTests(unittest.TestCase):
    def setUp(self):
        self.translation = AtomicTransform.translation(V(1, 2, 3))
        self.rotation = AtomicTransform.rotation(P(0, 0, 0), V(0, 0, 1), math.pi / 3)
        self.scale = AtomicTransform.scale(P(1, 1, 1), 2.5)
        self.reflection = AtomicTransform.reflection(AtomicPlane.world_xy())
        self.orient = AtomicTransform.orient(AtomicPlane.world_xy(), AtomicPlane.world_yz(P(2, 0, 0)))
        self.nonuniform = AtomicTransform.scale_non_uniform(AtomicPlane.world_xy(), 2.0, 0.5, 3.0)
        self.point = P(2, -1, 5)

    def test_matmul_applies_right_operand_first(self):
        composed = self.rotation @ self.translation
        expected = self.rotation.transform_point(self.translation.transform_point(self.point))
        close(self, composed.transform_point(self.point), expected)

    def test_compound_and_then_apply_in_list_order(self):
        compound = AtomicTransform.compound([self.translation, self.rotation, self.scale])
        chained = self.translation.then(self.rotation, self.scale)
        expected = self.scale.transform_point(self.rotation.transform_point(self.translation.transform_point(self.point)))
        close(self, compound.transform_point(self.point), expected)
        close(self, chained.transform_point(self.point), expected)
        self.assertTrue(AtomicTransform.compound([]).is_identity)

    def test_inverse_round_trips_for_every_invertible_factory(self):
        for name in ("translation", "rotation", "scale", "reflection", "orient", "nonuniform"):
            with self.subTest(factory=name):
                transform = getattr(self, name)
                self.assertTrue((transform @ transform.inverse()).is_identity)
                close(self, transform.inverse().transform_point(transform.transform_point(self.point)), self.point)

    def test_determinant_signs(self):
        self.assertAlmostEqual(self.rotation.determinant, 1.0)
        self.assertAlmostEqual(self.reflection.determinant, -1.0)
        self.assertAlmostEqual(self.scale.determinant, 2.5 ** 3)

    def test_transform_point_rejects_non_affine_matrices(self):
        projective = AtomicTransform(matrix=(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0.5, 1))
        self.assertFalse(projective.is_affine)
        with self.assertRaises(ValueError):
            projective.transform_point(self.point)

    def test_transform_vector_ignores_translation(self):
        close(self, self.translation.transform_vector(V(1, 0, 0)), V(1, 0, 0))


class FactoryTests(unittest.TestCase):
    def test_shear_fixes_base_plane_and_maps_grip_to_target(self):
        shear = AtomicTransform.shear(AtomicPlane.world_xy(), P(0, 0, 1), P(1, 0.5, 1))
        close(self, shear.transform_point(P(7, -3, 0)), P(7, -3, 0))
        close(self, shear.transform_point(P(0, 0, 1)), P(1, 0.5, 1))
        close(self, shear.transform_point(P(0, 0, 2)), P(2, 1.0, 2))
        with self.assertRaises(ValueError):
            AtomicTransform.shear(AtomicPlane.world_xy(), P(1, 1, 0), P(2, 2, 0))

    def test_projection_is_idempotent_and_lands_on_the_plane(self):
        plane = AtomicPlane.world_xy(P(0, 0, 2))
        projection = AtomicTransform.projection(plane)
        landed = projection.transform_point(P(3, 4, 9))
        close(self, landed, P(3, 4, 2))
        close(self, (projection @ projection).transform_point(P(3, 4, 9)), landed)
        self.assertAlmostEqual(projection.determinant, 0.0)
        with self.assertRaises(ValueError):
            projection.inverse()

    def test_oblique_projection_follows_the_direction(self):
        projection = AtomicTransform.projection(AtomicPlane.world_xy(), V(1, 0, -1))
        close(self, projection.transform_point(P(0, 0, 2)), P(2, 0, 0))
        with self.assertRaises(ValueError):
            AtomicTransform.projection(AtomicPlane.world_xy(), V(1, 0, 0))

    def test_rotation_to_direction(self):
        turn = AtomicTransform.rotation_to_direction(P(0, 0, 0), V(1, 0, 0), V(0, 0, 1))
        close(self, turn.transform_vector(V(1, 0, 0)), V(0, 0, 1))
        self.assertTrue(AtomicTransform.rotation_to_direction(P(0, 0, 0), V(2, 0, 0), V(5, 0, 0)).is_identity)
        flip = AtomicTransform.rotation_to_direction(P(0, 0, 0), V(1, 0, 0), V(-1, 0, 0))
        close(self, flip.transform_vector(V(1, 0, 0)), V(-1, 0, 0))
        close(self, AtomicTransform.plane_to_plane(AtomicPlane.world_xy(), AtomicPlane.world_xy(P(1, 0, 0))).transform_point(P(0, 0, 0)), P(1, 0, 0))


class ApplyTransformTests(unittest.TestCase):
    def test_projection_degrades_circle_to_nurbs_on_the_plane(self):
        circle = AtomicCircle(AtomicPlane.world_xz(), 1.0)
        flattened = apply_transform(AtomicTransform.projection(AtomicPlane.world_xy()), circle)
        self.assertIsInstance(flattened, AtomicNurbsCurve)
        self.assertTrue(all(abs(point.z) < 1e-12 for point in flattened.control_points))

    def test_projection_of_a_perpendicular_plane_raises_clearly(self):
        with self.assertRaises(ValueError) as context:
            apply_transform(AtomicTransform.projection(AtomicPlane.world_xy()), AtomicPlane.world_xz())
        self.assertIn("collapses the plane", str(context.exception))


if __name__ == "__main__":
    unittest.main()
