"""Shapely adapter for planar curve region booleans."""

from __future__ import annotations

import math
from typing import Iterable

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicControlPointCurve,
    AtomicEllipse,
    AtomicInterpolatedCurve,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicRectangle,
)
from pyhopper.Utils.Curves import evaluate_nurbs_curve, nurbs_curve_domain
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

try:
    from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Polygon
    from shapely.ops import polygonize, unary_union
    from shapely.validation import make_valid
except ImportError:  # pragma: no cover - exercised only without optional dependency
    GeometryCollection = LineString = MultiPolygon = Polygon = None  # type: ignore[assignment]
    polygonize = unary_union = make_valid = None  # type: ignore[assignment]


CurveLike = (
    AtomicArc
    | AtomicCircle
    | AtomicControlPointCurve
    | AtomicEllipse
    | AtomicInterpolatedCurve
    | AtomicLine
    | AtomicNurbsCurve
    | AtomicPolyline
    | AtomicRectangle
)

_AREA_TOLERANCE = 1e-10
_DISTANCE_TOLERANCE = 1e-7
_CURVE_SAMPLE_COUNT = 96


def _require_shapely() -> None:
    if (
        Polygon is None
        or LineString is None
        or MultiPolygon is None
        or GeometryCollection is None
        or polygonize is None
        or unary_union is None
        or make_valid is None
    ):
        raise RuntimeError("Region boolean components require Shapely to be installed")


def _dot(point: AtomicPoint, origin: AtomicPoint, axis) -> float:
    return (
        (point.x - origin.x) * axis.x
        + (point.y - origin.y) * axis.y
        + (point.z - origin.z) * axis.z
    )


def _point_to_plane_xy(point: AtomicPoint, plane: AtomicPlane) -> tuple[float, float]:
    return (
        _dot(point, plane.origin, plane.x_axis),
        _dot(point, plane.origin, plane.y_axis),
    )


def _point_from_plane_xy(x: float, y: float, plane: AtomicPlane) -> AtomicPoint:
    y_axis = plane.y_axis
    return AtomicPoint(
        plane.origin.x + x * plane.x_axis.x + y * y_axis.x,
        plane.origin.y + x * plane.x_axis.y + y * y_axis.y,
        plane.origin.z + x * plane.x_axis.z + y * y_axis.z,
    )


def _distance_2d(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _dedupe_consecutive(coords: Iterable[tuple[float, float]]) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []
    for coord in coords:
        point = (float(coord[0]), float(coord[1]))
        if not result or _distance_2d(result[-1], point) > _DISTANCE_TOLERANCE:
            result.append(point)
    return result


def _closed_ring(coords: Iterable[tuple[float, float]], source_name: str) -> list[tuple[float, float]]:
    ring = _dedupe_consecutive(coords)
    if len(ring) < 3:
        raise ValueError(f"{source_name} must define a closed region with at least three distinct points")

    if _distance_2d(ring[0], ring[-1]) <= _DISTANCE_TOLERANCE:
        ring[-1] = ring[0]
    else:
        raise ValueError(f"{source_name} must be closed for region booleans")

    if len(ring) < 4:
        raise ValueError(f"{source_name} must define a non-degenerate closed region")
    return ring


def _sample_nurbs_curve(curve: AtomicNurbsCurve) -> list[AtomicPoint]:
    start, end = nurbs_curve_domain(curve)
    boundaries = sorted({start, end, *(knot for knot in curve.knots if start < knot < end)})
    samples: list[AtomicPoint] = []
    span_count = max(1, len(boundaries) - 1)
    samples_per_span = max(2, math.ceil(_CURVE_SAMPLE_COUNT / span_count))

    for span_start, span_end in zip(boundaries, boundaries[1:]):
        for index in range(samples_per_span):
            if samples and index == 0:
                continue
            parameter = span_start + (span_end - span_start) * index / samples_per_span
            samples.append(evaluate_nurbs_curve(curve, parameter))
    samples.append(evaluate_nurbs_curve(curve, end))
    return samples


def _curve_ring(curve: CurveLike, plane: AtomicPlane) -> list[tuple[float, float]]:
    if isinstance(curve, AtomicLine):
        raise ValueError("Region booleans require closed planar curves; Line is open")

    if isinstance(curve, AtomicPolyline):
        return _closed_ring((_point_to_plane_xy(point, plane) for point in curve.points), "Polyline")

    if isinstance(curve, AtomicRectangle):
        half_x = abs(float(curve.x_size)) / 2.0
        half_y = abs(float(curve.y_size)) / 2.0
        y_axis = curve.plane.y_axis
        points = [
            AtomicPoint(
                curve.plane.origin.x + x * curve.plane.x_axis.x + y * y_axis.x,
                curve.plane.origin.y + x * curve.plane.x_axis.y + y * y_axis.y,
                curve.plane.origin.z + x * curve.plane.x_axis.z + y * y_axis.z,
            )
            for x, y in (
                (-half_x, -half_y),
                (half_x, -half_y),
                (half_x, half_y),
                (-half_x, half_y),
                (-half_x, -half_y),
            )
        ]
        return _closed_ring((_point_to_plane_xy(point, plane) for point in points), "Rectangle")

    nurbs = as_nurbs_curve(curve)
    return _closed_ring((_point_to_plane_xy(point, plane) for point in _sample_nurbs_curve(nurbs)), type(curve).__name__)


def _curve_line(curve: CurveLike, plane: AtomicPlane) -> list[tuple[float, float]]:
    if isinstance(curve, AtomicLine):
        return _dedupe_consecutive((_point_to_plane_xy(curve.start, plane), _point_to_plane_xy(curve.end, plane)))
    if isinstance(curve, AtomicPolyline):
        return _dedupe_consecutive(_point_to_plane_xy(point, plane) for point in curve.points)
    if isinstance(curve, AtomicRectangle):
        return _curve_ring(curve, plane)
    return _dedupe_consecutive(_point_to_plane_xy(point, plane) for point in _sample_nurbs_curve(as_nurbs_curve(curve)))


def _polygon_parts(geometry) -> list:
    _require_shapely()
    if geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry] if abs(float(geometry.area)) > _AREA_TOLERANCE else []
    if isinstance(geometry, MultiPolygon):
        return [
            polygon
            for polygon in geometry.geoms
            if abs(float(polygon.area)) > _AREA_TOLERANCE
        ]
    if isinstance(geometry, GeometryCollection):
        parts = []
        for item in geometry.geoms:
            parts.extend(_polygon_parts(item))
        return parts
    return []


def _valid_polygon_from_ring(ring: list[tuple[float, float]]):
    _require_shapely()
    polygon = Polygon(ring)
    if polygon.is_empty or abs(float(polygon.area)) <= _AREA_TOLERANCE:
        raise ValueError("Region boolean input curve has zero area")
    if not polygon.is_valid:
        polygon = make_valid(polygon)
    return _polygon_parts(polygon)


def _curves_to_geometry(curves: Iterable[CurveLike], plane: AtomicPlane):
    _require_shapely()
    polygons = []
    for curve in curves:
        polygons.extend(_valid_polygon_from_ring(_curve_ring(curve, plane)))

    if not polygons:
        return GeometryCollection()
    return unary_union(polygons)


def _ring_to_polyline(coords: Iterable[tuple[float, float]], plane: AtomicPlane) -> AtomicPolyline:
    ring = _dedupe_consecutive((float(x), float(y)) for x, y, *_ in coords)
    if len(ring) < 3:
        raise ValueError("Region boolean output produced a degenerate ring")
    if _distance_2d(ring[0], ring[-1]) > _DISTANCE_TOLERANCE:
        ring.append(ring[0])
    else:
        ring[-1] = ring[0]
    return AtomicPolyline(points=tuple(_point_from_plane_xy(x, y, plane) for x, y in ring))


def _geometry_to_curves(geometry, plane: AtomicPlane) -> list[AtomicPolyline]:
    curves: list[AtomicPolyline] = []
    for polygon in _polygon_parts(geometry):
        curves.append(_ring_to_polyline(polygon.exterior.coords, plane))
        curves.extend(_ring_to_polyline(ring.coords, plane) for ring in polygon.interiors)
    return curves


def _geometry_to_region_boundaries(geometry, plane: AtomicPlane) -> list[tuple[AtomicPolyline, tuple[AtomicPolyline, ...]]]:
    return [
        (
            _ring_to_polyline(polygon.exterior.coords, plane),
            tuple(_ring_to_polyline(ring.coords, plane) for ring in polygon.interiors),
        )
        for polygon in _polygon_parts(geometry)
    ]


def region_union(curves: Iterable[CurveLike], plane: AtomicPlane) -> list[AtomicPolyline]:
    """Return the union outlines of closed planar curves."""
    return _geometry_to_curves(_curves_to_geometry(curves, plane), plane)


def regions_from_boundary_edges(edges: Iterable[CurveLike], plane: AtomicPlane) -> list[AtomicPolyline]:
    """Return closed region outlines found by polygonizing boundary edge curves."""
    return [
        loop
        for outer, holes in region_boundaries_from_boundary_edges(edges, plane)
        for loop in (outer, *holes)
    ]


def region_boundaries_from_boundary_edges(edges: Iterable[CurveLike], plane: AtomicPlane) -> list[tuple[AtomicPolyline, tuple[AtomicPolyline, ...]]]:
    """Return closed region boundaries found by polygonizing boundary edge curves."""
    _require_shapely()
    lines = []
    for edge in edges:
        coords = _curve_line(edge, plane)
        if len(coords) < 2:
            continue
        lines.append(LineString(coords))

    if not lines:
        return []

    polygons = list(polygonize(lines))
    if not polygons:
        raise ValueError("BoundarySurfaces could not find closed planar regions from the supplied edges")
    return _geometry_to_region_boundaries(unary_union(polygons), plane)


def region_difference(curves_a: Iterable[CurveLike], curves_b: Iterable[CurveLike], plane: AtomicPlane) -> list[AtomicPolyline]:
    """Return the outlines of ``curves_a`` minus ``curves_b``."""
    _require_shapely()
    return _geometry_to_curves(_curves_to_geometry(curves_a, plane).difference(_curves_to_geometry(curves_b, plane)), plane)


def region_intersection(curves_a: Iterable[CurveLike], curves_b: Iterable[CurveLike], plane: AtomicPlane) -> list[AtomicPolyline]:
    """Return the intersection outlines of two closed planar curve sets."""
    _require_shapely()
    return _geometry_to_curves(_curves_to_geometry(curves_a, plane).intersection(_curves_to_geometry(curves_b, plane)), plane)
