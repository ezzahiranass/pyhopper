"""CurvesOnSurfaces - pulling, projecting and offsetting curves on surfaces
(Grasshopper's Pull Curve, Project Curve and Offset on Srf).

Rhino refits these curves with its own tolerance-driven algorithms; pyhopper
samples the curve, moves every sample onto the surface and interpolates the
runs of samples that land on it, so only the structure is comparable — except
on planar surfaces, where straight inputs give exact lines and polylines.
"""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicLine, AtomicNurbsCurve, AtomicPoint, AtomicPolyline, AtomicSurface, AtomicVector
from pyhopper.Utils.ClosestPoints import brep_faces, surface_closest_point, surface_line_hits
from pyhopper.Utils.Curves import curve_domain_of, curve_point_at, curve_tangent_at
from pyhopper.Utils.Interpolation import CHORD, rhino_interpolated_curve
from pyhopper.Utils.Nurbs import surface_domain, surface_normal
from pyhopper.Utils.Tolerances import ABSOLUTE_TOLERANCE
from pyhopper.Utils.Vectors import cross, distance, dot, is_zero, length, sub, unit

_ZERO = 1e-9


def _sample_parameters(curve, minimum: int = 32) -> list[float]:
    start, end = curve_domain_of(curve)
    if isinstance(curve, AtomicPolyline):
        count = len(curve.points) - 1
        per_segment = max(1, math.ceil(minimum / count))
        return [(i + j / per_segment) / count for i in range(count) for j in range(per_segment)] + [1.0]
    if isinstance(curve, AtomicNurbsCurve):
        spans = max(1, len(curve.control_points) - int(curve.degree))
        minimum = max(minimum, 16 * spans)
    return [start + (end - start) * i / minimum for i in range(minimum + 1)]


def _trace(curve, mapper) -> list[list[AtomicPoint]]:
    """Map every sample of *curve* through *mapper* (a point, or ``None`` where the sample leaves the
    surface) and return the runs of mapped points; where a run starts or ends between samples the
    boundary is refined by bisection so runs reach the surface edge."""
    parameters = _sample_parameters(curve)
    mapped = [mapper(t) for t in parameters]
    runs: list[list[AtomicPoint]] = []
    current: list[AtomicPoint] = []
    for index, (t, point) in enumerate(zip(parameters, mapped)):
        if point is None:
            if current:
                edge = _bisect_edge(mapper, parameters[index - 1], t)
                if edge is not None and distance(current[-1], edge) > _ZERO:
                    current.append(edge)
                if len(current) >= 2:
                    runs.append(current)
                current = []
            continue
        if not current and index > 0 and mapped[index - 1] is None:
            edge = _bisect_edge(mapper, t, parameters[index - 1])
            if edge is not None and distance(edge, point) > _ZERO:
                current.append(edge)
        if not current or distance(current[-1], point) > _ZERO:
            current.append(point)
    if len(current) >= 2:
        runs.append(current)
    return runs


def _bisect_edge(mapper, inside: float, outside: float, iterations: int = 25) -> AtomicPoint | None:
    """Between a mapped sample (*inside*) and an unmapped one (*outside*): the last mapped point found
    while bisecting towards the edge of the surface."""
    last = None
    for _ in range(iterations):
        middle = 0.5 * (inside + outside)
        point = mapper(middle)
        if point is None:
            outside = middle
        else:
            inside, last = middle, point
        if abs(outside - inside) <= 1e-12:
            break
    return last


def _collinear(points: list[AtomicPoint]) -> bool:
    direction = sub(points[-1], points[0])
    if is_zero(direction, _ZERO):
        return False
    axis = unit(direction)
    return all(length(cross(sub(p, points[0]), axis)) <= 1e-9 * max(1.0, length(direction)) for p in points)


def _fit_run(points: list[AtomicPoint]):
    if _collinear(points):
        return AtomicLine(points[0], points[-1])
    return rhino_interpolated_curve(points, CHORD)


def _surface_is_planar(surface: AtomicSurface) -> bool:
    (u0, u1), (v0, v1) = surface_domain(surface)
    normals = [surface_normal(surface, u0 + (u1 - u0) * i / 3, v0 + (v1 - v0) * j / 3) for i in range(4) for j in range(4)]
    return all(distance(normal, normals[0]) <= 1e-9 for normal in normals)


def _normal_projection_lands(point: AtomicPoint, closest: AtomicPoint, normal: AtomicVector, clamped: bool) -> bool:
    """A sample counts as being on the surface when its closest point is a normal projection (or the
    point sits on the surface); a point whose closest point is merely the nearest boundary is outside."""
    if not clamped:
        return True
    offset = sub(point, closest)
    if length(offset) <= ABSOLUTE_TOLERANCE:
        return True
    return length(cross(unit(offset), normal)) <= 1e-6


def pull_curve(curve, surface: AtomicSurface) -> list:
    """Grasshopper's Pull Curve: the curve moved onto the surface by closest points; the parts whose
    normal projection misses the surface are dropped, a curve already on the surface comes back as it is."""
    def mapper(t: float):
        point = curve_point_at(curve, t)
        u, v, closest, _, clamped = surface_closest_point(surface, point)
        return closest if _normal_projection_lands(point, closest, surface_normal(surface, u, v), clamped) else None

    already_there = True
    for t in _sample_parameters(curve):
        mapped = mapper(t)
        if mapped is None or distance(curve_point_at(curve, t), mapped) > 1e-9:
            already_there = False
            break
    if already_there:
        return [curve]
    return [_fit_run(run) for run in _trace(curve, mapper)]


def project_curve(curve, brep, direction: AtomicVector) -> list:
    """Grasshopper's Project Curve: every sample projected along the direction (either way) onto the
    nearest face hit; runs of hits become curves, misses split the result."""
    axis = unit(direction)
    if is_zero(axis):
        raise ValueError("Projection direction must not be zero")
    faces = brep_faces(brep)
    if not faces:
        raise TypeError("Project Curve needs a surface or brep to project onto")
    def mapper(t: float):
        point = curve_point_at(curve, t)
        hits = [hit for face in faces for hit in surface_line_hits(face, point, axis)]
        return min(hits, key=lambda hit: abs(hit[2]))[3] if hits else None

    return [_fit_run(run) for run in _trace(curve, mapper)]


def offset_on_surface(curve, offset_distance: float, surface: AtomicSurface) -> list:
    """Grasshopper's Offset on Srf: the curve moved sideways on the surface by the distance (to the
    left of its direction seen along the surface normal). Straight curves on planar surfaces offset
    exactly (polyline corners are mitred); other cases move samples along the in-surface perpendicular,
    pull them back onto the surface and interpolate."""
    d = float(offset_distance)
    if abs(d) <= _ZERO:
        return [curve]
    planar = _surface_is_planar(surface)
    if planar and isinstance(curve, (AtomicLine, AtomicPolyline)):
        (u0, u1), (v0, v1) = surface_domain(surface)
        normal = surface_normal(surface, 0.5 * (u0 + u1), 0.5 * (v0 + v1))
        points = list(curve.points) if isinstance(curve, AtomicPolyline) else [curve.start, curve.end]
        return [AtomicPolyline(tuple(_offset_polyline_points(points, d, normal)))]
    def mapper(t: float):
        point = curve_point_at(curve, t)
        tangent = curve_tangent_at(curve, t)
        u, v, closest, _, clamped = surface_closest_point(surface, point)
        normal = surface_normal(surface, u, v)
        sideways = cross(normal, tangent)
        if is_zero(sideways, _ZERO):
            return None
        sideways = unit(sideways)
        target = AtomicPoint(closest.x + sideways.x * d, closest.y + sideways.y * d, closest.z + sideways.z * d)
        u, v, pulled, _, clamped = surface_closest_point(surface, target)
        return pulled if _normal_projection_lands(target, pulled, surface_normal(surface, u, v), clamped) else None

    return [_fit_run(run) for run in _trace(curve, mapper)]


def _offset_polyline_points(points: list[AtomicPoint], d: float, normal: AtomicVector) -> list[AtomicPoint]:
    """Mitred offset of a polyline lying in the plane with *normal*, to the left of its direction."""
    closed = len(points) > 2 and distance(points[0], points[-1]) <= _ZERO
    vertices = points[:-1] if closed else points
    count = len(vertices)
    directions = []
    for i in range(count - (0 if closed else 1)):
        a, b = vertices[i], vertices[(i + 1) % count]
        directions.append(unit(sub(b, a)))
    result: list[AtomicPoint] = []
    for i, vertex in enumerate(vertices):
        incoming = directions[i - 1] if (i > 0 or closed) else None
        outgoing = directions[i] if (i < count - 1 or closed) else None
        if incoming is None:
            side = unit(cross(normal, outgoing))
            result.append(AtomicPoint(vertex.x + side.x * d, vertex.y + side.y * d, vertex.z + side.z * d))
        elif outgoing is None:
            side = unit(cross(normal, incoming))
            result.append(AtomicPoint(vertex.x + side.x * d, vertex.y + side.y * d, vertex.z + side.z * d))
        else:
            side_in, side_out = unit(cross(normal, incoming)), unit(cross(normal, outgoing))
            bisector = AtomicVector(side_in.x + side_out.x, side_in.y + side_out.y, side_in.z + side_out.z)
            if is_zero(bisector, _ZERO):
                result.append(AtomicPoint(vertex.x + side_in.x * d, vertex.y + side_in.y * d, vertex.z + side_in.z * d))
                continue
            bisector = unit(bisector)
            stretch = d / max(dot(bisector, side_in), 1e-9)
            result.append(AtomicPoint(vertex.x + bisector.x * stretch, vertex.y + bisector.y * stretch, vertex.z + bisector.z * stretch))
    if closed:
        result.append(result[0])
    return result
