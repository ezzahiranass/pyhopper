"""Surface kernel vs RhinoCommon: points, normals, first derivatives."""

from __future__ import annotations

import unittest

from oracle.support import assert_close, assert_parallel, load, requires_rhino, to_nurbs_surface

from pyhopper.Utils.Nurbs import surface_derivatives, surface_domain, surface_normal, surface_point

UV = ((0.05, 0.1), (0.25, 0.5), (0.4, 0.9), (0.66, 0.33), (0.9, 0.75), (1.0, 0.5))


def _sample_surfaces():
    from tests.test_nurbs import sample_surfaces

    return sample_surfaces()


@requires_rhino
class SurfaceOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.Rhino = load()
        cls.surfaces = _sample_surfaces()

    def _pairs(self):
        for name, surface in self.surfaces.items():
            rhino_surface = to_nurbs_surface(surface)
            self.assertTrue(rhino_surface.IsValid, f"{name}: RhinoCommon rejected the converted surface")
            yield name, surface, rhino_surface

    def _parameters(self, surface, rhino_surface):
        (u0, u1), (v0, v1) = surface_domain(surface)
        self.assertAlmostEqual(rhino_surface.Domain(0).T0, u0, places=12)
        self.assertAlmostEqual(rhino_surface.Domain(0).T1, u1, places=12)
        self.assertAlmostEqual(rhino_surface.Domain(1).T0, v0, places=12)
        self.assertAlmostEqual(rhino_surface.Domain(1).T1, v1, places=12)
        for s, t in UV:
            yield u0 + (u1 - u0) * s, v0 + (v1 - v0) * t

    def test_points(self) -> None:
        for name, surface, rhino_surface in self._pairs():
            for u, v in self._parameters(surface, rhino_surface):
                with self.subTest(surface=name, u=u, v=v):
                    assert_close(self, surface_point(surface, u, v), rhino_surface.PointAt(u, v), 1e-9, "point")

    def test_normals_and_first_derivatives(self) -> None:
        for name, surface, rhino_surface in self._pairs():
            for u, v in self._parameters(surface, rhino_surface):
                with self.subTest(surface=name, u=u, v=v):
                    ok, point, derivatives = rhino_surface.Evaluate(u, v, 1)
                    self.assertTrue(ok)
                    ours = surface_derivatives(surface, u, v, 1)
                    assert_close(self, ours.du, derivatives[0], 1e-6, "du")
                    assert_close(self, ours.dv, derivatives[1], 1e-6, "dv")
                    rhino_normal = rhino_surface.NormalAt(u, v)
                    if rhino_normal.Length > 0.5:  # Rhino returns a zero vector at degenerate poles
                        assert_parallel(self, surface_normal(surface, u, v), rhino_normal, 1e-6, "normal")


if __name__ == "__main__":
    unittest.main()
