"""AtomicTransform factories vs RhinoCommon Transform."""

from __future__ import annotations

import math
import unittest

from oracle.support import assert_close, load, requires_rhino, to_plane, to_point, to_vector

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicTransform, AtomicVector

P = AtomicPoint
V = AtomicVector
SAMPLE_POINTS = (P(0, 0, 0), P(1, 2, 3), P(-4, 0.5, 2), P(3, -3, -1), P(0.25, 7, 0))


@requires_rhino
class TransformOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.Rhino = load()

    def _compare(self, ours: AtomicTransform, theirs, tolerance: float = 1e-9) -> None:
        for point in SAMPLE_POINTS:
            rhino_point = to_point(point)
            rhino_point.Transform(theirs)
            assert_close(self, ours.transform_point(point), rhino_point, tolerance, f"point {point}")

    def test_rotation(self) -> None:
        theirs = self.Rhino.Geometry.Transform.Rotation(math.radians(37.0), to_vector(V(1, 2, 0.5)), to_point(P(1, 1, 1)))
        self._compare(AtomicTransform.rotation(P(1, 1, 1), V(1, 2, 0.5), math.radians(37.0)), theirs)

    def test_plane_to_plane_orient(self) -> None:
        source = AtomicPlane.world_xy(P(1, 2, 3))
        target = AtomicPlane(P(-2, 0, 5), V(0, 1, 1), V(1, 0, 0))
        theirs = self.Rhino.Geometry.Transform.PlaneToPlane(to_plane(source), to_plane(target))
        self._compare(AtomicTransform.orient(source, target), theirs)

    def test_mirror(self) -> None:
        plane = AtomicPlane(P(0, 1, 0), V(0, 1, 0.2), V(1, 0, 0))
        theirs = self.Rhino.Geometry.Transform.Mirror(to_plane(plane))
        self._compare(AtomicTransform.reflection(plane), theirs)

    def test_planar_projection(self) -> None:
        plane = AtomicPlane(P(0, 0, 2), V(0.3, 0, 1), V(1, 0, 0))
        theirs = self.Rhino.Geometry.Transform.PlanarProjection(to_plane(plane))
        self._compare(AtomicTransform.projection(plane), theirs)

    def test_projection_along_direction(self) -> None:
        plane = AtomicPlane.world_xy(P(0, 0, 1))
        direction = V(1, 0.5, -2)
        theirs = self.Rhino.Geometry.Transform.ProjectAlong(to_plane(plane), to_vector(direction))
        self._compare(AtomicTransform.projection(plane, direction), theirs)

    def test_shear_matches_rhino_shear_with_equivalent_axes(self) -> None:
        base = AtomicPlane.world_xy()
        grip, target = P(0, 0, 2), P(1, 0.5, 2)
        ours = AtomicTransform.shear(base, grip, target)
        # Rhino's Shear maps the plane axes to the given vectors: z goes to z + (target - grip) / grip height.
        theirs = self.Rhino.Geometry.Transform.Shear(
            to_plane(base),
            to_vector(V(1, 0, 0)),
            to_vector(V(0, 1, 0)),
            to_vector(V(0.5, 0.25, 1)),
        )
        self._compare(ours, theirs)

    def test_scale_uniform_and_non_uniform(self) -> None:
        theirs = self.Rhino.Geometry.Transform.Scale(to_point(P(1, 2, 3)), 2.5)
        self._compare(AtomicTransform.scale(P(1, 2, 3), 2.5), theirs)
        plane = AtomicPlane(P(1, 0, 0), V(0, 0, 1), V(1, 1, 0))
        theirs = self.Rhino.Geometry.Transform.Scale(to_plane(plane), 2.0, 0.5, 3.0)
        self._compare(AtomicTransform.scale_non_uniform(plane, 2.0, 0.5, 3.0), theirs)

    def test_inverse_and_composition_against_rhino(self) -> None:
        rotation = AtomicTransform.rotation(P(0, 0, 0), V(0, 0, 1), 1.1)
        translation = AtomicTransform.translation(V(1, 2, 3))
        theirs = self.Rhino.Geometry.Transform.Rotation(1.1, to_vector(V(0, 0, 1)), to_point(P(0, 0, 0))) * self.Rhino.Geometry.Transform.Translation(to_vector(V(1, 2, 3)))
        self._compare(rotation @ translation, theirs)
        ok, inverse = theirs.TryGetInverse()
        self.assertTrue(ok)
        self._compare((rotation @ translation).inverse(), inverse)


if __name__ == "__main__":
    unittest.main()
