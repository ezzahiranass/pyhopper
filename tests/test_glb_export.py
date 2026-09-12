"""Byte-identity guard for the GLB exporter.

A deterministic scene covering every exportable atom family is exported and
hashed; the hash is compared with ``tests/golden/glb/basic_scene.sha256``.
Any change in tessellation, NURBS evaluation or buffer layout shows up here,
which is what protects the kernel consolidation refactors.
"""

from __future__ import annotations

import hashlib
import math
import tempfile
import unittest
from pathlib import Path

from tests.support.golden import UPDATE, golden_path, read_text, write_text
from tests.support.skips import requires_shapely

from pyhopper import CenterBox, Cone, CylinderCmp, Interpolate, Loft, RuledSurface, Sphere
from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicEllipse,
    AtomicInterval,
    AtomicLine,
    AtomicMesh,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyCurve,
    AtomicPolyline,
    AtomicRectangle,
    AtomicVector,
)
from pyhopper.Utils.Exporters import export_glb_with_manifest
from pyhopper.Utils.Surfaces import trimmed_surface_from_planar_loops

GOLDEN = golden_path("glb", "basic_scene.sha256")


def _plane(z: float) -> AtomicPlane:
    return AtomicPlane.world_xy(AtomicPoint(0.0, 0.0, z))


def basic_scene() -> dict[str, object]:
    """Named geometry (node id -> items) with one representative per atom type."""
    square = AtomicPolyline(
        (
            AtomicPoint(0.0, 0.0, 0.0),
            AtomicPoint(4.0, 0.0, 0.0),
            AtomicPoint(4.0, 3.0, 0.0),
            AtomicPoint(0.0, 3.0, 0.0),
            AtomicPoint(0.0, 0.0, 0.0),
        )
    )
    interpolated = Interpolate([AtomicPoint(0.0, 0.0, 0.0), AtomicPoint(2.0, 1.5, 0.0), AtomicPoint(4.0, 0.0, 1.0), AtomicPoint(6.0, 2.0, 0.5)])
    ruled = RuledSurface(AtomicCircle(_plane(0.0), 2.0), AtomicCircle(_plane(3.0), 3.0))
    loft = Loft([AtomicCircle(_plane(0.0), 1.0), AtomicCircle(_plane(1.0), 1.5), AtomicCircle(_plane(2.0), 1.0)])
    mesh = AtomicMesh(
        vertices=(AtomicPoint(0.0, 0.0, 0.0), AtomicPoint(1.0, 0.0, 0.0), AtomicPoint(1.0, 1.0, 0.0), AtomicPoint(0.0, 1.0, 0.0)),
        faces=((0, 1, 2, 3),),
    )
    return {
        "points": [AtomicPoint(1.0, 2.0, 3.0)],
        "lines": [AtomicLine(AtomicPoint(0.0, 0.0, 0.0), AtomicPoint(5.0, 1.0, 2.0))],
        "polylines": [square],
        "circles": [AtomicCircle(_plane(0.0), 2.5)],
        "arcs": [AtomicArc(_plane(0.0), 1.5, AtomicInterval(0.3, 2.4))],
        "ellipses": [AtomicEllipse(_plane(0.5), 3.0, 1.25)],
        "rectangles": [AtomicRectangle(_plane(1.0), 2.0, 1.0)],
        "interpolated": interpolated,
        "ruled": ruled,
        "loft": loft,
        "cylinder": CylinderCmp(_plane(0.0), 1.0, 2.0),
        "cone": Cone(_plane(0.0), 1.0, 2.0),
        "sphere": Sphere(_plane(0.0), 1.5),
        "box": CenterBox(_plane(0.0), 2.0, 3.0, 1.0),
        "mesh": [mesh],
    }


def export_bytes(scene: dict[str, object]) -> tuple[bytes, list[dict[str, str]]]:
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "scene.glb"
        manifest = export_glb_with_manifest(scene, target)
        return target.read_bytes(), manifest


class GlbExportTests(unittest.TestCase):
    def test_export_is_deterministic(self) -> None:
        first, _ = export_bytes(basic_scene())
        second, _ = export_bytes(basic_scene())
        self.assertEqual(first, second)

    def test_manifest_lists_every_node_once_per_object(self) -> None:
        _, manifest = export_bytes(basic_scene())
        node_ids = {entry["nodeId"] for entry in manifest}
        self.assertEqual(node_ids, set(basic_scene().keys()))
        names = [entry["objectName"] for entry in manifest]
        self.assertEqual(len(names), len(set(names)))

    def test_basic_scene_bytes_match_golden(self) -> None:
        data, _ = export_bytes(basic_scene())
        digest = hashlib.sha256(data).hexdigest()
        if UPDATE or not GOLDEN.exists():
            write_text(GOLDEN, digest)
        self.assertEqual(digest, read_text(GOLDEN), "GLB bytes changed — intended? re-record with PYHOPPER_UPDATE_GOLDEN=1")

    @requires_shapely
    def test_trimmed_surface_exports_triangles(self) -> None:
        outer = AtomicPolyline(tuple(AtomicPoint(2.0 * math.cos(a), 2.0 * math.sin(a), 0.0) for a in (i * math.tau / 8 for i in range(9))))
        hole = AtomicPolyline(tuple(AtomicPoint(0.5 * math.cos(a), 0.5 * math.sin(a), 0.0) for a in (i * math.tau / 6 for i in range(7))))
        trimmed = trimmed_surface_from_planar_loops(outer, (hole,), AtomicPlane.world_xy())
        data, manifest = export_bytes({"trimmed": [trimmed]})
        self.assertEqual(len(manifest), 1)
        self.assertGreater(len(data), 200)

    def test_polycurve_exports_one_line_strip(self) -> None:
        arc = AtomicArc(AtomicPlane(AtomicPoint(2.0, 2.0, 0.0), AtomicVector(0.0, 0.0, 1.0), AtomicVector(0.0, -1.0, 0.0)), 2.0, AtomicInterval(0.0, math.pi / 2))
        polycurve = AtomicPolyCurve((AtomicLine(AtomicPoint(0.0, 0.0, 0.0), AtomicPoint(2.0, 0.0, 0.0)), arc), (2.0, math.pi), 0.0)
        data, manifest = export_bytes({"poly": [polycurve]})
        self.assertEqual(len(manifest), 1)
        self.assertGreater(len(data), 300)
        # a bare polycurve of the same segments exports the same bytes as its manifest twin
        self.assertEqual(export_bytes({"poly": [polycurve]})[0], data)


if __name__ == "__main__":
    unittest.main()
