"""Bounding boxes of pyhopper geometry, aligned to a plane (Grasshopper Bounding Box).

Extents are measured in the plane's coordinates. Points, lines, polylines,
rectangles, boxes and meshes are exact; circles and arcs are exact through
their analytic extrema; NURBS curves and surfaces use their control nets — a
conservative hull, so Grasshopper's tight curve boxes can be smaller (recorded
as a deviation until the kernel samples curves).
"""

from __future__ import annotations

import math
from typing import Iterable

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicBox,
    AtomicBrep,
    AtomicCircle,
    AtomicControlPointCurve,
    AtomicCylinder,
    AtomicEllipse,
    AtomicInterpolatedCurve,
    AtomicLine,
    AtomicMesh,
    AtomicNurbsCurve,
    AtomicPolyCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicRectangle,
    AtomicSurface,
    AtomicTrimmedSurface,
)
from pyhopper.Utils.Boxes import box_corners
from pyhopper.Utils.Planes import plane_coordinates, point_on_plane
from pyhopper.Utils.Vectors import dot

Extents = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]


def _extents(coordinates: Iterable[tuple[float, float, float]]) -> Extents | None:
    xs, ys, zs = [], [], []
    for x, y, z in coordinates:
        xs.append(x)
        ys.append(y)
        zs.append(z)
    if not xs:
        return None
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def _merge(a: Extents | None, b: Extents | None) -> Extents | None:
    if a is None:
        return b
    if b is None:
        return a
    return tuple((min(lo_a, lo_b), max(hi_a, hi_b)) for (lo_a, hi_a), (lo_b, hi_b) in zip(a, b))  # type: ignore[return-value]


def _arc_extents(plane: AtomicPlane, arc, start: float, sweep: float) -> Extents:
    """Exact extents of an arc/circle: its ends plus every extremum of each plane axis inside the sweep."""
    centre = arc.plane.origin
    radius = float(arc.radius)
    x_axis, y_axis = arc.plane.x_axis, arc.plane.y_axis
    angles = {start, start + sweep}
    for axis in (plane.x_axis, plane.y_axis, plane.normal):
        # d/dθ (cosθ a + sinθ b)·axis = 0  ->  tanθ = (b·axis)/(a·axis)
        a_dot, b_dot = dot(x_axis, axis), dot(y_axis, axis)
        if abs(a_dot) < 1e-15 and abs(b_dot) < 1e-15:
            continue
        theta = math.atan2(b_dot, a_dot)
        for candidate in (theta, theta + math.pi):
            # bring the candidate into the swept interval, whichever direction it runs
            low, high = (start, start + sweep) if sweep >= 0 else (start + sweep, start)
            k = math.floor((low - candidate) / (2.0 * math.pi))
            for turn in (k, k + 1, k + 2):
                angle = candidate + 2.0 * math.pi * turn
                if low - 1e-12 <= angle <= high + 1e-12:
                    angles.add(angle)
    points = [
        AtomicPoint(
            centre.x + radius * (math.cos(t) * x_axis.x + math.sin(t) * y_axis.x),
            centre.y + radius * (math.cos(t) * x_axis.y + math.sin(t) * y_axis.y),
            centre.z + radius * (math.cos(t) * x_axis.z + math.sin(t) * y_axis.z),
        )
        for t in angles
    ]
    return _extents(plane_coordinates(plane, point) for point in points)  # type: ignore[return-value]


def geometry_extents(geometry, plane: AtomicPlane) -> Extents | None:
    """((x0, x1), (y0, y1), (z0, z1)) of ``geometry`` in ``plane`` coordinates, or None for nothing."""
    if isinstance(geometry, AtomicPoint):
        return _extents([plane_coordinates(plane, geometry)])
    if isinstance(geometry, AtomicLine):
        return _extents(plane_coordinates(plane, p) for p in (geometry.start, geometry.end))
    if isinstance(geometry, AtomicPolyline):
        return _extents(plane_coordinates(plane, p) for p in geometry.points)
    if isinstance(geometry, AtomicRectangle):
        half_x, half_y = float(geometry.x_size) / 2.0, float(geometry.y_size) / 2.0
        corners = [point_on_plane(geometry.plane, sx * half_x, sy * half_y) for sx in (-1, 1) for sy in (-1, 1)]
        return _extents(plane_coordinates(plane, p) for p in corners)
    if isinstance(geometry, AtomicBox):
        return _extents(plane_coordinates(plane, p) for p in box_corners(geometry))
    if isinstance(geometry, AtomicCircle):
        return _arc_extents(plane, geometry, 0.0, 2.0 * math.pi)
    if isinstance(geometry, AtomicArc):
        return _arc_extents(plane, geometry, float(geometry.angle.start), float(geometry.angle.length))
    if isinstance(geometry, AtomicMesh):
        return _extents(plane_coordinates(plane, p) for p in geometry.vertices)
    if isinstance(geometry, AtomicNurbsCurve):
        return _extents(plane_coordinates(plane, p) for p in geometry.control_points)
    if isinstance(geometry, AtomicSurface):
        return _extents(plane_coordinates(plane, p) for row in geometry.poles for p in row)
    if isinstance(geometry, AtomicTrimmedSurface):
        return geometry_extents(geometry.surface, plane)
    if isinstance(geometry, AtomicBrep):
        result = None
        for face in geometry.faces:
            result = _merge(result, geometry_extents(face, plane))
        return result
    if isinstance(geometry, AtomicPolyCurve):
        result = None
        for segment in geometry.segments:
            result = _merge(result, geometry_extents(segment, plane))
        return result
    if isinstance(geometry, (AtomicEllipse, AtomicInterpolatedCurve, AtomicControlPointCurve)):
        from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

        return geometry_extents(as_nurbs_curve(geometry), plane)
    if isinstance(geometry, AtomicCylinder):
        # exact: the two rim circles (the base sits on the cylinder plane, the top ``height`` along its normal)
        top_plane = AtomicPlane(origin=point_on_plane(geometry.plane, 0.0, 0.0, float(geometry.height)), normal=geometry.plane.normal, x_axis=geometry.plane.x_axis)
        return _merge(
            geometry_extents(AtomicCircle(geometry.plane, geometry.radius), plane),
            geometry_extents(AtomicCircle(top_plane, geometry.radius), plane),
        )
    if isinstance(geometry, AtomicPlane):
        raise TypeError("Bounding Box cannot measure an infinite plane")
    raise TypeError(f"Bounding Box cannot measure {type(geometry).__name__}")


def box_from_extents(plane: AtomicPlane, extents: Extents) -> AtomicBox:
    """Box aligned to ``plane`` spanning ``extents`` (plane coordinates), centred like every pyhopper box."""
    (x0, x1), (y0, y1), (z0, z1) = extents
    centre = point_on_plane(plane, (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
    return AtomicBox(AtomicPlane(origin=centre, normal=plane.normal, x_axis=plane.x_axis), x1 - x0, y1 - y0, z1 - z0)


def plane_space_box(extents: Extents) -> AtomicBox:
    """The same extents as a box sitting in plane space (world axes) — Grasshopper's second Bounding Box output."""
    (x0, x1), (y0, y1), (z0, z1) = extents
    centre = AtomicPoint((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
    return AtomicBox(AtomicPlane.world_xy(centre), x1 - x0, y1 - y0, z1 - z0)


def bounding_boxes(items: Iterable, plane: AtomicPlane, union: bool = False) -> tuple[list[AtomicBox], list[AtomicBox]]:
    """(world boxes, plane-space boxes): one pair per item, or a single pair for all with ``union``."""
    extents_list = [geometry_extents(item, plane) for item in items]
    if union:
        merged = None
        for extents in extents_list:
            merged = _merge(merged, extents)
        extents_list = [merged] if merged is not None else []
    world = [box_from_extents(plane, extents) for extents in extents_list if extents is not None]
    local = [plane_space_box(extents) for extents in extents_list if extents is not None]
    return world, local


def minimum_signed_distance(geometry, plane: AtomicPlane) -> float:
    """Lowest signed distance of ``geometry`` above ``plane`` (negative when it dips below)."""
    extents = geometry_extents(geometry, plane)
    if extents is None:
        raise ValueError("Cannot measure the distance of empty geometry to a plane")
    return extents[2][0]


def tight_extents(geometry, plane: AtomicPlane, samples: int = 96) -> Extents | None:
    """Like :func:`geometry_extents` but NURBS curves and surfaces are sampled densely instead of
    measured by their control points, so the box hugs the geometry (Grasshopper's Plane Through Shape)."""
    from pyhopper.Utils.Nurbs import curve_domain, curve_point, surface_domain, surface_point

    if isinstance(geometry, AtomicSurface):
        (u0, u1), (v0, v1) = surface_domain(geometry)
        points = [surface_point(geometry, u0 + (u1 - u0) * i / samples, v0 + (v1 - v0) * j / samples) for i in range(samples + 1) for j in range(samples + 1)]
        return _extents(plane_coordinates(plane, p) for p in points)
    if isinstance(geometry, AtomicTrimmedSurface):
        return tight_extents(geometry.surface, plane, samples)
    if isinstance(geometry, AtomicBrep):
        result = None
        for face in geometry.faces:
            result = _merge(result, tight_extents(face, plane, samples))
        return result
    if isinstance(geometry, AtomicPolyCurve):
        result = None
        for segment in geometry.segments:
            result = _merge(result, tight_extents(segment, plane, samples))
        return result
    if isinstance(geometry, (AtomicNurbsCurve, AtomicEllipse, AtomicInterpolatedCurve, AtomicControlPointCurve)):
        from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

        curve = as_nurbs_curve(geometry)
        start, end = curve_domain(curve)
        count = samples * max(1, len(curve.control_points))
        return _extents(plane_coordinates(plane, curve_point(curve, start + (end - start) * i / count)) for i in range(count + 1))
    return geometry_extents(geometry, plane)
