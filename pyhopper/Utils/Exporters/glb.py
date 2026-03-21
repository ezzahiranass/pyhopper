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
  AtomicSurface   -> tessellated triangle mesh

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
_SURFACE_SUBDIVS_PER_SPAN = {1: 1, 2: 16, 3: 12}


def export_glb(tree: Any, filepath: str | FilePath) -> None:
    """Export *tree* (DataTree or plain list of Atoms) to a .glb file."""
    builder = _GlbBuilder()
    for atom in _iter_atoms(tree):
        builder.add_atom(atom)

    data = builder.build()
    FilePath(filepath).write_bytes(data)


def export_glb_with_manifest(
    named_geometry: dict[str, Any],
    filepath: str | FilePath,
) -> list[dict[str, str]]:
    """Export one GLB while preserving object-to-node provenance."""
    builder = _GlbBuilder()
    manifest: list[dict[str, str]] = []

    for node_id, geometry in named_geometry.items():
        local_index = 0
        for atom in _iter_atoms(geometry):
            object_name = f"{_safe_object_name(node_id)}_{local_index:03d}"
            if builder.add_atom(atom, name=object_name):
                manifest.append({
                    "objectName": object_name,
                    "nodeId": node_id,
                })
                local_index += 1

    data = builder.build()
    FilePath(filepath).write_bytes(data)
    return manifest


def _iter_atoms(tree: Any) -> list[Any]:
    """Return a flat list of supported atoms from DataTree/list/scalar geometry."""
    from pyhopper.Core.Atoms import (
        AtomicBrep,
        AtomicCircle,
        AtomicCylinder,
        AtomicLine,
        AtomicMesh,
        AtomicPoint,
        AtomicPolyline,
        AtomicSurface,
    )
    from pyhopper.Core.DataTree import DataTree

    if isinstance(tree, DataTree):
        atoms = tree.all_items()
    elif isinstance(tree, (list, tuple)):
        atoms = list(tree)
    else:
        atoms = [tree]

    supported_atom_types = (
        AtomicPolyline,
        AtomicLine,
        AtomicCylinder,
        AtomicMesh,
        AtomicPoint,
        AtomicCircle,
        AtomicSurface,
        AtomicBrep,
    )
    return [atom for atom in atoms if isinstance(atom, supported_atom_types)]


def _safe_object_name(node_id: str) -> str:
    slug = "".join(char if char.isalnum() else "_" for char in node_id).strip("_").lower()
    return f"ph_{slug or 'node'}"


class _GlbBuilder:
    """Accumulates glTF meshes and serialises to binary glTF."""

    def __init__(self):
        self._bin: bytearray = bytearray()
        self._accessors: list[dict] = []
        self._buffer_views: list[dict] = []
        self._meshes: list[dict] = []
        self._nodes: list[dict] = []

    def add_atom(self, atom: Any, name: str | None = None) -> bool:
        from pyhopper.Core.Atoms import (
            AtomicBrep,
            AtomicCircle,
            AtomicCylinder,
            AtomicLine,
            AtomicMesh,
            AtomicPoint,
            AtomicPolyline,
            AtomicSurface,
        )

        if isinstance(atom, AtomicPolyline):
            self.add_polyline(atom, name=name)
            return True
        if isinstance(atom, AtomicLine):
            self.add_line(atom, name=name)
            return True
        if isinstance(atom, AtomicCylinder):
            self.add_cylinder(atom, name=name)
            return True
        if isinstance(atom, AtomicMesh):
            return self.add_mesh(atom, name=name)
        if isinstance(atom, AtomicPoint):
            self.add_point(atom, name=name)
            return True
        if isinstance(atom, AtomicCircle):
            self.add_circle(atom, name=name)
            return True
        if isinstance(atom, AtomicSurface):
            return self.add_surface(atom, name=name)
        if isinstance(atom, AtomicBrep):
            return self.add_brep(atom, name=name)
        return False

    def add_point(self, pt, name: str | None = None) -> None:
        positions = [(pt.x, pt.y, pt.z)]
        acc_idx = self._add_vec3_accessor(positions)
        self._push_mesh({"attributes": {"POSITION": acc_idx}, "mode": _POINTS}, name=name)

    def add_polyline(self, poly, name: str | None = None) -> None:
        if not poly.points:
            return
        positions = [(p.x, p.y, p.z) for p in poly.points]
        acc_idx = self._add_vec3_accessor(positions)
        self._push_mesh({"attributes": {"POSITION": acc_idx}, "mode": _LINE_STRIP}, name=name)

    def add_line(self, line, name: str | None = None) -> None:
        positions = [
            (line.start.x, line.start.y, line.start.z),
            (line.end.x, line.end.y, line.end.z),
        ]
        acc_idx = self._add_vec3_accessor(positions)
        self._push_mesh({"attributes": {"POSITION": acc_idx}, "mode": _LINE_STRIP}, name=name)

    def add_circle(self, circle, name: str | None = None) -> None:
        positions = _circle_points(circle, _CIRCLE_SEGS)
        acc_idx = self._add_vec3_accessor(positions)
        self._push_mesh({"attributes": {"POSITION": acc_idx}, "mode": _LINE_STRIP}, name=name)

    def add_mesh(self, mesh, name: str | None = None) -> bool:
        if not mesh.vertices or not mesh.faces:
            return False
        positions = [(v.x, v.y, v.z) for v in mesh.vertices]
        indices = _triangulate_faces(mesh.faces)
        if not indices:
            return False
        pos_acc = self._add_vec3_accessor(positions)
        idx_acc = self._add_index_accessor(indices)
        self._push_mesh({
            "attributes": {"POSITION": pos_acc},
            "indices": idx_acc,
            "mode": _TRIANGLES,
        }, name=name)
        return True

    def add_cylinder(self, cyl, name: str | None = None) -> None:
        positions, indices = _tessellate_cylinder(cyl, _CYLINDER_SEGS)
        pos_acc = self._add_vec3_accessor(positions)
        idx_acc = self._add_index_accessor(indices)
        self._push_mesh({
            "attributes": {"POSITION": pos_acc},
            "indices": idx_acc,
            "mode": _TRIANGLES,
        }, name=name)

    def add_brep(self, brep, name: str | None = None) -> bool:
        """Tessellate all Brep faces and emit them as a single merged mesh."""
        all_positions: list[tuple[float, float, float]] = []
        all_indices: list[int] = []

        for face in brep.faces:
            face_positions, face_indices = _tessellate_surface(face)
            if not face_positions:
                continue
            offset = len(all_positions)
            all_positions.extend(face_positions)
            all_indices.extend(idx + offset for idx in face_indices)

        if not all_positions or not all_indices:
            return False

        pos_acc = self._add_vec3_accessor(all_positions)
        idx_acc = self._add_index_accessor(all_indices)
        self._push_mesh({
            "attributes": {"POSITION": pos_acc},
            "indices": idx_acc,
            "mode": _TRIANGLES,
        }, name=name)
        return True

    def add_surface(self, surface, name: str | None = None) -> bool:
        positions, indices = _tessellate_surface(surface)
        if not positions or not indices:
            return False
        pos_acc = self._add_vec3_accessor(positions)
        idx_acc = self._add_index_accessor(indices)
        self._push_mesh({
            "attributes": {"POSITION": pos_acc},
            "indices": idx_acc,
            "mode": _TRIANGLES,
        }, name=name)
        return True

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

    def _push_mesh(self, primitive: dict, name: str | None = None) -> None:
        mesh_idx = len(self._meshes)
        self._meshes.append({"primitives": [primitive]})
        node = {"mesh": mesh_idx}
        if name:
            node["name"] = name
        self._nodes.append(node)

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


def _expand_knots(knots: tuple[float, ...], mults: tuple[int, ...]) -> tuple[float, ...]:
    expanded = []
    for knot, mult in zip(knots, mults):
        expanded.extend([float(knot)] * int(mult))
    return tuple(expanded)


def _find_span(degree: int, knots: tuple[float, ...], control_point_count: int, parameter: float) -> int:
    if parameter >= knots[control_point_count]:
        return control_point_count - 1
    if parameter <= knots[degree]:
        return degree

    low = degree
    high = control_point_count
    mid = (low + high) // 2
    while parameter < knots[mid] or parameter >= knots[mid + 1]:
        if parameter < knots[mid]:
            high = mid
        else:
            low = mid
        mid = (low + high) // 2
    return mid


def _basis_functions(span: int, parameter: float, degree: int, knots: tuple[float, ...]) -> list[float]:
    basis = [0.0] * (degree + 1)
    basis[0] = 1.0
    left = [0.0] * (degree + 1)
    right = [0.0] * (degree + 1)

    for j in range(1, degree + 1):
        left[j] = parameter - knots[span + 1 - j]
        right[j] = knots[span + j] - parameter
        saved = 0.0
        for r in range(j):
            denominator = right[r + 1] + left[j - r]
            term = 0.0 if abs(denominator) < 1e-12 else basis[r] / denominator
            basis[r] = saved + right[r + 1] * term
            saved = left[j - r] * term
        basis[j] = saved

    return basis


def _surface_point(surface, u: float, v: float) -> tuple[float, float, float]:
    poles = surface.poles
    weights = surface.weights
    v_count = len(poles)
    u_count = len(poles[0])

    u_knots = _expand_knots(surface.u_knots, surface.u_mults)
    v_knots = _expand_knots(surface.v_knots, surface.v_mults)
    u_degree = max(1, min(int(surface.u_degree), u_count - 1))
    v_degree = max(1, min(int(surface.v_degree), v_count - 1))

    u_min = u_knots[u_degree]
    u_max = u_knots[u_count]
    v_min = v_knots[v_degree]
    v_max = v_knots[v_count]

    uu = max(u_min, min(u_max, u))
    vv = max(v_min, min(v_max, v))

    u_span = _find_span(u_degree, u_knots, u_count, uu)
    v_span = _find_span(v_degree, v_knots, v_count, vv)
    u_basis = _basis_functions(u_span, uu, u_degree, u_knots)
    v_basis = _basis_functions(v_span, vv, v_degree, v_knots)

    x = y = z = w = 0.0
    for l in range(v_degree + 1):
        row_index = v_span - v_degree + l
        for k in range(u_degree + 1):
            col_index = u_span - u_degree + k
            point = poles[row_index][col_index]
            weight = weights[row_index][col_index]
            coeff = u_basis[k] * v_basis[l] * weight
            x += coeff * point.x
            y += coeff * point.y
            z += coeff * point.z
            w += coeff

    if abs(w) < 1e-12:
        return 0.0, 0.0, 0.0
    return x / w, y / w, z / w


def _surface_parameter_samples(knots: tuple[float, ...], mults: tuple[int, ...], degree: int) -> list[float]:
    """Build parameter samples that respect knot span boundaries.

    Each knot span gets subdivisions proportional to the degree so that
    linear (degree-1) directions produce only the minimum needed samples
    while curved spans get enough interior points.
    """
    full_knots = _expand_knots(knots, mults)
    cp_count = len(full_knots) - degree - 1
    start = full_knots[degree]
    end = full_knots[cp_count]

    if end <= start:
        return [start, end]

    # Collect unique knot values in the active range as span boundaries.
    span_breaks = [start]
    for k in full_knots[degree + 1:cp_count + 1]:
        if k > span_breaks[-1]:
            span_breaks.append(k)
    if span_breaks[-1] < end:
        span_breaks.append(end)

    subdivs = _SURFACE_SUBDIVS_PER_SPAN.get(degree, max(6, degree * 2))

    samples: list[float] = []
    for i in range(len(span_breaks) - 1):
        a, b = span_breaks[i], span_breaks[i + 1]
        for j in range(subdivs):
            samples.append(a + (b - a) * j / subdivs)
    samples.append(span_breaks[-1])

    return samples


def _tessellate_surface(surface) -> tuple[list[tuple[float, float, float]], list[int]]:
    if not surface.poles or len(surface.poles) < 2 or len(surface.poles[0]) < 2:
        return [], []

    u_samples = _surface_parameter_samples(surface.u_knots, surface.u_mults, surface.u_degree)
    v_samples = _surface_parameter_samples(surface.v_knots, surface.v_mults, surface.v_degree)

    positions = []
    for vv in v_samples:
        for uu in u_samples:
            positions.append(_surface_point(surface, uu, vv))

    width = len(u_samples)
    height = len(v_samples)
    indices = []
    for row in range(height - 1):
        for col in range(width - 1):
            a = row * width + col
            b = a + 1
            c = a + width
            d = c + 1
            indices += [a, b, d, a, d, c]

    return positions, indices


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
