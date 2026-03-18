"""
GLB exporter for pyhopper DataTrees.

Converts a DataTree of Atom primitives into a binary glTF 2.0 (.glb) file.

Supported atoms
---------------
  AtomicPolyline  -> LINE_STRIP primitive (geometry only, no material needed)
  AtomicLine      -> LINE_STRIP primitive (2 points)
  AtomicCylinder  -> tessellated triangle mesh
  AtomicMesh      -> triangle mesh (faces must be triangles or quads; quads split)
  AtomicPoint     -> POINTS primitive
  AtomicCircle    -> tessellated LINE_STRIP (36 segments)

Unknown atom types are silently skipped.
"""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path as FilePath
from typing import Any

_GLB_MAGIC = 0x46546C67
_GLB_VERSION = 2
_CHUNK_JSON = 0x4E4F534A
_CHUNK_BIN = 0x004E4942

_FLOAT = 5126
_USHORT = 5123
_UINT = 5125
_POINTS = 0
_LINE_STRIP = 3
_TRIANGLES = 4

_CYLINDER_SEGS = 32
_CIRCLE_SEGS = 64


def export_glb(tree: Any, filepath: str | FilePath) -> None:
    """Export *tree* (DataTree or plain list of Atoms) to a .glb file."""
    from pyhopper.Core.Atoms import (
        AtomicCircle,
        AtomicCylinder,
        AtomicLine,
        AtomicMesh,
        AtomicPoint,
        AtomicPolyline,
    )
    from pyhopper.Core.DataTree import DataTree

    if isinstance(tree, DataTree):
        atoms = tree.all_items()
    elif isinstance(tree, (list, tuple)):
        atoms = list(tree)
    else:
        atoms = [tree]

    builder = _GlbBuilder()

    for atom in atoms:
        if isinstance(atom, AtomicPolyline):
            builder.add_polyline(atom)
        elif isinstance(atom, AtomicLine):
            builder.add_line(atom)
        elif isinstance(atom, AtomicCylinder):
            builder.add_cylinder(atom)
        elif isinstance(atom, AtomicMesh):
            builder.add_mesh(atom)
        elif isinstance(atom, AtomicPoint):
            builder.add_point(atom)
        elif isinstance(atom, AtomicCircle):
            builder.add_circle(atom)

    data = builder.build()
    FilePath(filepath).write_bytes(data)


class _GlbBuilder:
    """Accumulates glTF meshes and serialises to binary glTF."""

    def __init__(self):
        self._bin: bytearray = bytearray()
        self._accessors: list[dict] = []
        self._buffer_views: list[dict] = []
        self._meshes: list[dict] = []
        self._nodes: list[dict] = []

    def add_point(self, pt) -> None:
        positions = [(pt.x, pt.y, pt.z)]
        acc_idx = self._add_vec3_accessor(positions)
        self._push_mesh({"attributes": {"POSITION": acc_idx}, "mode": _POINTS})

    def add_polyline(self, poly) -> None:
        if not poly.points:
            return
        positions = [(p.x, p.y, p.z) for p in poly.points]
        acc_idx = self._add_vec3_accessor(positions)
        self._push_mesh({"attributes": {"POSITION": acc_idx}, "mode": _LINE_STRIP})

    def add_line(self, line) -> None:
        positions = [
            (line.start.x, line.start.y, line.start.z),
            (line.end.x, line.end.y, line.end.z),
        ]
        acc_idx = self._add_vec3_accessor(positions)
        self._push_mesh({"attributes": {"POSITION": acc_idx}, "mode": _LINE_STRIP})

    def add_circle(self, circle) -> None:
        positions = _circle_points(circle, _CIRCLE_SEGS)
        acc_idx = self._add_vec3_accessor(positions)
        self._push_mesh({"attributes": {"POSITION": acc_idx}, "mode": _LINE_STRIP})

    def add_mesh(self, mesh) -> None:
        if not mesh.vertices or not mesh.faces:
            return
        positions = [(v.x, v.y, v.z) for v in mesh.vertices]
        indices = _triangulate_faces(mesh.faces)
        if not indices:
            return
        pos_acc = self._add_vec3_accessor(positions)
        idx_acc = self._add_index_accessor(indices)
        self._push_mesh({
            "attributes": {"POSITION": pos_acc},
            "indices": idx_acc,
            "mode": _TRIANGLES,
        })

    def add_cylinder(self, cyl) -> None:
        positions, indices = _tessellate_cylinder(cyl, _CYLINDER_SEGS)
        pos_acc = self._add_vec3_accessor(positions)
        idx_acc = self._add_index_accessor(indices)
        self._push_mesh({
            "attributes": {"POSITION": pos_acc},
            "indices": idx_acc,
            "mode": _TRIANGLES,
        })

    def _add_vec3_accessor(self, points: list[tuple[float, float, float]]) -> int:
        byte_offset = len(self._bin)
        for x, y, z in points:
            self._bin += struct.pack("<fff", x, y, z)
        byte_length = len(self._bin) - byte_offset

        bv_idx = len(self._buffer_views)
        self._buffer_views.append({
            "buffer": 0,
            "byteOffset": byte_offset,
            "byteLength": byte_length,
            "target": 34962,
        })

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        zs = [p[2] for p in points]

        acc_idx = len(self._accessors)
        self._accessors.append({
            "bufferView": bv_idx,
            "byteOffset": 0,
            "componentType": _FLOAT,
            "count": len(points),
            "type": "VEC3",
            "min": [min(xs), min(ys), min(zs)],
            "max": [max(xs), max(ys), max(zs)],
        })
        return acc_idx

    def _add_index_accessor(self, indices: list[int]) -> int:
        if len(self._bin) % 4 != 0:
            self._bin += b"\x00" * (4 - len(self._bin) % 4)

        byte_offset = len(self._bin)
        use_uint = max(indices) > 65535
        if use_uint:
            for index in indices:
                self._bin += struct.pack("<I", index)
            comp_type = _UINT
        else:
            for index in indices:
                self._bin += struct.pack("<H", index)
            if len(indices) % 2 != 0:
                self._bin += b"\x00\x00"
            comp_type = _USHORT

        byte_length = len(self._bin) - byte_offset

        bv_idx = len(self._buffer_views)
        self._buffer_views.append({
            "buffer": 0,
            "byteOffset": byte_offset,
            "byteLength": byte_length,
            "target": 34963,
        })

        acc_idx = len(self._accessors)
        self._accessors.append({
            "bufferView": bv_idx,
            "byteOffset": 0,
            "componentType": comp_type,
            "count": len(indices),
            "type": "SCALAR",
        })
        return acc_idx

    def _push_mesh(self, primitive: dict) -> None:
        mesh_idx = len(self._meshes)
        self._meshes.append({"primitives": [primitive]})
        self._nodes.append({"mesh": mesh_idx})

    def build(self) -> bytes:
        while len(self._bin) % 4 != 0:
            self._bin += b"\x00"

        gltf = {
            "asset": {"version": "2.0", "generator": "pyhopper"},
            "scene": 0,
            "scenes": [{"nodes": list(range(len(self._nodes)))}],
            "nodes": self._nodes,
            "meshes": self._meshes,
            "accessors": self._accessors,
            "bufferViews": self._buffer_views,
            "buffers": [{"byteLength": len(self._bin)}],
        }

        json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
        while len(json_bytes) % 4 != 0:
            json_bytes += b" "

        total = 12 + 8 + len(json_bytes) + 8 + len(self._bin)

        out = bytearray()
        out += struct.pack("<III", _GLB_MAGIC, _GLB_VERSION, total)
        out += struct.pack("<II", len(json_bytes), _CHUNK_JSON)
        out += json_bytes
        out += struct.pack("<II", len(self._bin), _CHUNK_BIN)
        out += self._bin
        return bytes(out)


def _circle_points(circle, segments: int) -> list[tuple[float, float, float]]:
    """Return closed ring of points for an AtomicCircle atom."""
    cx = circle.plane.origin.x
    cy = circle.plane.origin.y
    cz = circle.plane.origin.z
    xx, xy, xz = circle.plane.x_axis.x, circle.plane.x_axis.y, circle.plane.x_axis.z
    yx, yy, yz = circle.plane.y_axis.x, circle.plane.y_axis.y, circle.plane.y_axis.z
    radius = circle.radius
    points = []
    for index in range(segments + 1):
        t = 2 * math.pi * index / segments
        cos_t, sin_t = math.cos(t), math.sin(t)
        points.append((
            cx + radius * (cos_t * xx + sin_t * yx),
            cy + radius * (cos_t * xy + sin_t * yy),
            cz + radius * (cos_t * xz + sin_t * yz),
        ))
    return points


def _tessellate_cylinder(cyl, segments: int) -> tuple[list[tuple[float, float, float]], list[int]]:
    """Tessellate an AtomicCylinder atom into vertices and triangle indices."""
    ox = cyl.plane.origin.x
    oy = cyl.plane.origin.y
    oz = cyl.plane.origin.z
    xx, xy, xz = cyl.plane.x_axis.x, cyl.plane.x_axis.y, cyl.plane.x_axis.z
    yx, yy, yz = cyl.plane.y_axis.x, cyl.plane.y_axis.y, cyl.plane.y_axis.z
    nx, ny, nz = cyl.plane.normal.x, cyl.plane.normal.y, cyl.plane.normal.z
    radius, height = cyl.radius, cyl.height

    bottom_ring = []
    top_ring = []
    for index in range(segments):
        t = 2 * math.pi * index / segments
        cos_t, sin_t = math.cos(t), math.sin(t)
        bx = ox + radius * (cos_t * xx + sin_t * yx)
        by = oy + radius * (cos_t * xy + sin_t * yy)
        bz = oz + radius * (cos_t * xz + sin_t * yz)
        bottom_ring.append((bx, by, bz))
        top_ring.append((bx + height * nx, by + height * ny, bz + height * nz))

    bottom_center = (ox, oy, oz)
    top_center = (ox + height * nx, oy + height * ny, oz + height * nz)

    vertices = bottom_ring + top_ring + [bottom_center, top_center]
    bottom_center_index = len(vertices) - 2
    top_center_index = len(vertices) - 1

    indices = []
    for index in range(segments):
        next_index = (index + 1) % segments
        indices += [index, next_index, segments + next_index, index, segments + next_index, segments + index]
        indices += [bottom_center_index, next_index, index]
        indices += [top_center_index, segments + index, segments + next_index]

    return vertices, indices


def _triangulate_faces(faces) -> list[int]:
    """Convert arbitrary-polygon face list to triangle index list."""
    indices = []
    for face in faces:
        if len(face) == 3:
            indices.extend(face)
        elif len(face) == 4:
            a, b, c, d = face
            indices += [a, b, c, a, c, d]
        else:
            for index in range(1, len(face) - 1):
                indices += [face[0], face[index], face[index + 1]]
    return indices
