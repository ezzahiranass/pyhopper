from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pyhopper import AtomicLine, AtomicPoint, AtomicTrimmedSurface, BoundarySurfaces, FourPointSurface, atom_from_json
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path as TreePath
from pyhopper.Utils.Exporters import export_glb


def rectangle_edges(x0: float, y0: float, x1: float, y1: float) -> list[AtomicLine]:
    a = AtomicPoint(x0, y0, 0.0)
    b = AtomicPoint(x1, y0, 0.0)
    c = AtomicPoint(x1, y1, 0.0)
    d = AtomicPoint(x0, y1, 0.0)
    return [
        AtomicLine(a, b),
        AtomicLine(b, c),
        AtomicLine(c, d),
        AtomicLine(d, a),
    ]


def closed_edges(points: list[AtomicPoint]) -> list[AtomicLine]:
    return [
        AtomicLine(start, end)
        for start, end in zip(points, [*points[1:], points[0]])
    ]


class SurfaceFreeformComponentTests(unittest.TestCase):
    def test_four_point_surface_creates_bilinear_patch(self):
        a = AtomicPoint(0, 0, 0)
        b = AtomicPoint(2, 0, 0)
        c = AtomicPoint(2, 1, 0)
        d = AtomicPoint(0, 1, 0)

        result = FourPointSurface(a, b, c, d)
        surface = result.all_items()[0]

        self.assertEqual(surface.poles, ((a, b), (d, c)))
        self.assertEqual(surface.u_degree, 1)
        self.assertEqual(surface.v_degree, 1)

    def test_four_point_surface_accepts_three_corners(self):
        a = AtomicPoint(0, 0, 0)
        b = AtomicPoint(1, 0, 0)
        c = AtomicPoint(0, 1, 0)

        surface = FourPointSurface(a, b, c).all_items()[0]

        self.assertEqual(surface.poles, ((a, b), (c, c)))

    def test_boundary_surfaces_creates_surface_from_closed_edge_set(self):
        result = BoundarySurfaces(rectangle_edges(0, 0, 2, 1))
        surface = result.all_items()[0]

        self.assertEqual(len(result.all_items()), 1)
        self.assertEqual(len(surface.poles), 2)
        self.assertEqual(len(surface.poles[0]), 2)
        self.assertEqual(surface.u_degree, 1)
        self.assertEqual(surface.v_degree, 1)

    def test_boundary_surfaces_preserves_branch_paths(self):
        tree = DataTree.from_branches({
            TreePath(0): rectangle_edges(0, 0, 1, 1),
            TreePath(2): rectangle_edges(0, 0, 2, 1),
        })

        result = BoundarySurfaces(tree)

        # LIST-only component: one call per branch, paths are kept (Grasshopper does the same)
        self.assertEqual(result.paths, tree.paths)
        self.assertEqual(len(result.branch(TreePath(0))), 1)
        self.assertEqual(len(result.branch(TreePath(2))), 1)

    def test_boundary_surfaces_outputs_trimmed_surface_for_non_quad_region(self):
        pentagon = closed_edges([
            AtomicPoint(0, 0, 0),
            AtomicPoint(2, 0, 0),
            AtomicPoint(2, 1, 0),
            AtomicPoint(1, 1.5, 0),
            AtomicPoint(0, 1, 0),
        ])

        surface = BoundarySurfaces(pentagon).all_items()[0]

        self.assertIsInstance(surface, AtomicTrimmedSurface)
        self.assertEqual(len(surface.outer.points), 6)
        restored = atom_from_json(surface.to_json())
        self.assertEqual(restored, surface)

    def test_trimmed_surface_exports_to_glb(self):
        pentagon = closed_edges([
            AtomicPoint(0, 0, 0),
            AtomicPoint(2, 0, 0),
            AtomicPoint(2, 1, 0),
            AtomicPoint(1, 1.5, 0),
            AtomicPoint(0, 1, 0),
        ])
        surface = BoundarySurfaces(pentagon)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "trimmed.glb"
            export_glb(surface, output_path)
            self.assertGreater(output_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
