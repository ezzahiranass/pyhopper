"""ClosestPoints - closest points on curves and surfaces, curve/curve and
curve/line proximity, ray casts onto surfaces, planar point-in-curve tests,
curve sides and extremes (the K3 kernel of the component roadmap).

Analytic where the atom allows it (lines, polylines, arcs, circles), otherwise
coarse sampling followed by Newton iterations on the NURBS form. Parameters
are always the atom's own (see ``Utils/Curves.py``).
"""

from __future__ import annotations

import math
from typing import Sequence

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicBox,
    AtomicBrep,
    AtomicCircle,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyCurve,
    AtomicPolyline,
    AtomicRectangle,
    AtomicSurface,
    AtomicTrimmedSurface,
    AtomicVector,
)
from pyhopper.Core.TypeSystem import CURVE_TYPES
from pyhopper.Utils.Curves import (
    curve_derivatives_at,
    curve_domain_of,
    curve_is_closed,
    curve_planarity,
    curve_point_at,
    curve_tangent_at,
    polycurve_breaks,
    segment_parameter,
)
from pyhopper.Utils.Nurbs import curve_derivatives, surface_derivatives, surface_domain
from pyhopper.Utils.Planes import plane_coordinates, point_on_plane, project_point
from pyhopper.Utils.Tolerances import ABSOLUTE_TOLERANCE
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Utils.Vectors import cross, distance, dot, is_zero, length, scale, sub, unit

_ZERO = 1e-12


def _to_vector(a) -> AtomicVector:
    return AtomicVector(float(a.x), float(a.y), float(a.z))


# ── curves ─────────────────────────────────────────────────────────


def _line_parameter(start: AtomicPoint, end: AtomicPoint, point: AtomicPoint) -> float:
    direction = sub(end, start)
    denominator = dot(direction, direction)
    if denominator <= _ZERO:
        return 0.0
    return min(1.0, max(0.0, dot(sub(point, start), direction) / denominator))


def _arc_closest(curve, point: AtomicPoint) -> tuple[float, AtomicPoint]:
    """Closest parameter on an arc or circle: the polar angle of the point in the arc plane; for an arc
    the angle is taken relative to the arc's middle and clamped to the sweep the way Rhino does (a point
    exactly opposite the middle lands on the arc's end). A point on the axis gives the start."""
    plane = curve.plane
    x, y, _ = plane_coordinates(plane, point)
    if abs(x) <= _ZERO and abs(y) <= _ZERO:
        return 0.0, curve_point_at(curve, 0.0)
    angle = math.atan2(y, x)
    if isinstance(curve, AtomicCircle):
        t = (angle % (2.0 * math.pi)) / (2.0 * math.pi)
        return t, curve_point_at(curve, t)
    start, sweep = float(curve.angle.start), float(curve.angle.length)
    if abs(sweep) <= _ZERO:
        return 0.0, curve_point_at(curve, 0.0)
    middle = start + 0.5 * sweep
    relative = (angle - middle) % (2.0 * math.pi)
    if relative > math.pi:
        relative -= 2.0 * math.pi
    clamped = min(max(middle + relative, min(start, start + sweep)), max(start, start + sweep))
    t = (clamped - start) / sweep
    return t, curve_point_at(curve, t)


def _nurbs_closest(nurbs: AtomicNurbsCurve, point: AtomicPoint) -> tuple[float, AtomicPoint]:
    start, end = curve_domain_of(nurbs)
    spans = max(1, len(nurbs.control_points) - int(nurbs.degree))
    samples = max(16, 8 * spans)
    candidates = [start + (end - start) * i / samples for i in range(samples + 1)]
    distances = [distance(curve_point_at(nurbs, t), point) for t in candidates]
    # refine every local minimum of the sampled distances (plus the ends) with Newton
    seeds = [candidates[i] for i in range(len(candidates)) if (i == 0 or distances[i] <= distances[i - 1]) and (i == len(candidates) - 1 or distances[i] <= distances[i + 1])]
    best_t, best_point = candidates[0], curve_point_at(nurbs, candidates[0])
    best = distances[0]
    for seed in seeds:
        t = seed
        for _ in range(40):
            c, (first, second) = curve_derivatives(nurbs, t, 2)
            offset = sub(c, point)
            f = dot(first, offset)
            df = dot(second, offset) + dot(first, first)
            if abs(df) <= _ZERO:
                break
            step = f / df
            t_new = min(end, max(start, t - step))
            if abs(t_new - t) <= 1e-14 * max(1.0, abs(end - start)):
                t = t_new
                break
            t = t_new
        p = curve_point_at(nurbs, t)
        d = distance(p, point)
        if d < best - 1e-15:
            best, best_t, best_point = d, t, p
    return best_t, best_point


def curve_closest_point(curve, point: AtomicPoint) -> tuple[float, AtomicPoint, float]:
    """``(parameter, point on curve, distance)`` of the point of *curve* closest to *point* (the
    atom's own parameterisation; ties go to the earliest parameter)."""
    if isinstance(curve, AtomicLine):
        t = _line_parameter(curve.start, curve.end, point)
        p = curve_point_at(curve, t)
        return t, p, distance(p, point)
    if isinstance(curve, AtomicPolyline):
        count = len(curve.points) - 1
        best = None
        for index, (a, b) in enumerate(zip(curve.points, curve.points[1:])):
            local = _line_parameter(a, b, point)
            p = AtomicPoint(a.x + (b.x - a.x) * local, a.y + (b.y - a.y) * local, a.z + (b.z - a.z) * local)
            d = distance(p, point)
            if best is None or d < best[2] - _ZERO:
                best = ((index + local) / count, p, d)
        return best
    if isinstance(curve, (AtomicArc, AtomicCircle)):
        t, p = _arc_closest(curve, point)
        return t, p, distance(p, point)
    if isinstance(curve, AtomicPolyCurve):
        breaks = polycurve_breaks(curve)
        best = None
        for index, segment in enumerate(curve.segments):
            t, p, d = curve_closest_point(segment, point)
            seg_start, seg_end = curve_domain_of(segment)
            local = 0.0 if seg_end - seg_start <= _ZERO else (t - seg_start) / (seg_end - seg_start)
            parameter = breaks[index] + (breaks[index + 1] - breaks[index]) * local
            if best is None or d < best[2] - _ZERO:
                best = (parameter, p, d)
        return best
    if isinstance(curve, AtomicRectangle):
        t, p, d = curve_closest_point(AtomicPolyline(as_nurbs_curve(curve).control_points), point)
        return t, p, d
    nurbs = as_nurbs_curve(curve)
    t, p = _nurbs_closest(nurbs, point)
    return t, p, distance(p, point)


def curve_curve_closest(curve_a, curve_b, samples: int = 64) -> tuple[float, float, AtomicPoint, AtomicPoint, float]:
    """Closest pair of points between two curves: the best sampled pair refined by alternating
    closest-point projections. Returns ``(t_a, t_b, point_a, point_b, distance)``."""
    a0, a1 = curve_domain_of(curve_a)
    b0, b1 = curve_domain_of(curve_b)
    points_a = [(a0 + (a1 - a0) * i / samples, curve_point_at(curve_a, a0 + (a1 - a0) * i / samples)) for i in range(samples + 1)]
    points_b = [(b0 + (b1 - b0) * j / samples, curve_point_at(curve_b, b0 + (b1 - b0) * j / samples)) for j in range(samples + 1)]
    best_pair = min(((ta, tb, pa, pb) for ta, pa in points_a for tb, pb in points_b), key=lambda item: distance(item[2], item[3]))
    ta, tb, pa, pb = best_pair
    for _ in range(60):
        tb_new, pb_new, _ = curve_closest_point(curve_b, pa)
        ta_new, pa_new, d = curve_closest_point(curve_a, pb_new)
        converged = abs(ta_new - ta) <= 1e-13 * max(1.0, abs(a1 - a0)) and abs(tb_new - tb) <= 1e-13 * max(1.0, abs(b1 - b0))
        ta, tb, pa, pb = ta_new, tb_new, pa_new, pb_new
        if converged:
            break
    return ta, tb, pa, pb, distance(pa, pb)


def curve_line_closest(curve, origin: AtomicPoint, direction: AtomicVector, samples: int = 64) -> tuple[float, float, AtomicPoint, AtomicPoint, float]:
    """Closest pair between a curve and the infinite line ``origin + s·direction``:
    ``(t, s, point on curve, point on line, distance)``."""
    axis = unit(direction)
    a0, a1 = curve_domain_of(curve)

    def line_point(p):
        s = dot(sub(p, origin), axis)
        return s, AtomicPoint(origin.x + axis.x * s, origin.y + axis.y * s, origin.z + axis.z * s)

    best = None
    for i in range(samples + 1):
        t = a0 + (a1 - a0) * i / samples
        p = curve_point_at(curve, t)
        s, q = line_point(p)
        d = distance(p, q)
        if best is None or d < best[4]:
            best = (t, s, p, q, d)
    t, s, p, q, d = best
    for _ in range(60):
        t_new, p_new, _ = curve_closest_point(curve, q)
        s_new, q_new = line_point(p_new)
        converged = abs(t_new - t) <= 1e-13 * max(1.0, abs(a1 - a0))
        t, s, p, q = t_new, s_new, p_new, q_new
        if converged:
            break
    return t, s, p, q, distance(p, q)


# ── surfaces ───────────────────────────────────────────────────────


def surface_closest_point(surface: AtomicSurface, point: AtomicPoint) -> tuple[float, float, AtomicPoint, float, bool]:
    """``(u, v, point on surface, distance, clamped)`` for the point of *surface* closest to *point*;
    ``clamped`` tells that the closest point sits on the boundary because the interior solution left
    the domain (the normal projection misses the surface)."""
    (u0, u1), (v0, v1) = surface_domain(surface)
    grid = 8
    candidates = [(u0 + (u1 - u0) * i / grid, v0 + (v1 - v0) * j / grid) for i in range(grid + 1) for j in range(grid + 1)]
    scored = sorted(candidates, key=lambda uv: distance(surface_derivatives(surface, uv[0], uv[1], 1).point, point))
    best = None
    for u, v in scored[:4]:
        u, v, clamped = _surface_newton(surface, point, u, v, (u0, u1), (v0, v1))
        p = surface_derivatives(surface, u, v, 1).point
        d = distance(p, point)
        if best is None or d < best[3] - 1e-15:
            best = (u, v, p, d, clamped)
    return best


def _surface_newton(surface, point, u, v, u_domain, v_domain) -> tuple[float, float, bool]:
    (u0, u1), (v0, v1) = u_domain, v_domain
    clamped = False
    for _ in range(60):
        ders = surface_derivatives(surface, u, v, 2)
        offset = sub(ders.point, point)
        fu, fv = dot(ders.du, offset), dot(ders.dv, offset)
        juu = dot(ders.du, ders.du) + dot(ders.duu, offset)
        juv = dot(ders.du, ders.dv) + dot(ders.duv, offset)
        jvv = dot(ders.dv, ders.dv) + dot(ders.dvv, offset)
        det = juu * jvv - juv * juv
        if abs(det) <= _ZERO:
            break
        du = (fu * jvv - fv * juv) / det
        dv = (juu * fv - juv * fu) / det
        u_new, v_new = u - du, v - dv
        clamped_now = not (u0 <= u_new <= u1 and v0 <= v_new <= v1)
        u_new, v_new = min(u1, max(u0, u_new)), min(v1, max(v0, v_new))
        if clamped_now:
            clamped = True
        if abs(u_new - u) <= 1e-14 * max(1.0, u1 - u0) and abs(v_new - v) <= 1e-14 * max(1.0, v1 - v0):
            u, v = u_new, v_new
            break
        u, v = u_new, v_new
    if clamped:
        # the minimum lies on an edge: minimise along the boundary curve(s) the point was pushed onto
        on_u = u <= u0 + _ZERO or u >= u1 - _ZERO
        on_v = v <= v0 + _ZERO or v >= v1 - _ZERO
        if on_u:
            v = _edge_newton(surface, point, u, v, False, v_domain)
        if on_v:
            u = _edge_newton(surface, point, u, v, True, u_domain)
    return u, v, clamped


def _edge_newton(surface, point, u, v, along_u: bool, domain) -> float:
    lo, hi = domain
    t = u if along_u else v
    for _ in range(60):
        ders = surface_derivatives(surface, u if not along_u else t, v if along_u else t, 2)
        first = ders.du if along_u else ders.dv
        second = ders.duu if along_u else ders.dvv
        offset = sub(ders.point, point)
        f = dot(first, offset)
        df = dot(second, offset) + dot(first, first)
        if abs(df) <= _ZERO:
            break
        t_new = min(hi, max(lo, t - f / df))
        if abs(t_new - t) <= 1e-14 * max(1.0, hi - lo):
            t = t_new
            break
        t = t_new
    return t


def surface_line_hits(surface: AtomicSurface, origin: AtomicPoint, direction: AtomicVector) -> list[tuple[float, float, float, AtomicPoint]]:
    """Intersections of the infinite line ``origin + s·direction`` with the surface, as
    ``(u, v, s, point)`` sorted by ``s`` (Newton from a grid of seeds, duplicates merged)."""
    axis = unit(direction)
    if is_zero(axis):
        raise ValueError("Projection direction must not be zero")
    (u0, u1), (v0, v1) = surface_domain(surface)
    # two directions perpendicular to the axis: the residual lives in their plane
    e1 = unit(cross(axis, AtomicVector(0.0, 0.0, 1.0) if abs(axis.z) < 0.9 else AtomicVector(1.0, 0.0, 0.0)))
    e2 = cross(axis, e1)
    grid = 5
    hits: list[tuple[float, float, float, AtomicPoint]] = []
    for i in range(grid + 1):
        for j in range(grid + 1):
            u, v = u0 + (u1 - u0) * i / grid, v0 + (v1 - v0) * j / grid
            for _ in range(40):
                ders = surface_derivatives(surface, u, v, 1)
                offset = sub(ders.point, origin)
                g1, g2 = dot(offset, e1), dot(offset, e2)
                j11, j12 = dot(ders.du, e1), dot(ders.dv, e1)
                j21, j22 = dot(ders.du, e2), dot(ders.dv, e2)
                det = j11 * j22 - j12 * j21
                if abs(det) <= _ZERO:
                    break
                du = (g1 * j22 - g2 * j12) / det
                dv = (j11 * g2 - j21 * g1) / det
                # the evaluator clamps into the domain, so keep the iterate inside it too
                u_new, v_new = min(u1, max(u0, u - du)), min(v1, max(v0, v - dv))
                step = max(abs(u_new - u), abs(v_new - v))
                u, v = u_new, v_new
                if step <= 1e-13 * max(1.0, u1 - u0, v1 - v0):
                    break
            p = surface_derivatives(surface, u, v, 1).point
            offset = sub(p, origin)
            if math.hypot(dot(offset, e1), dot(offset, e2)) > 1e-9 * max(1.0, length(offset)):
                continue
            s = dot(offset, axis)
            if all(abs(s - other[2]) > 1e-9 * max(1.0, abs(s)) or distance(p, other[3]) > 1e-9 for other in hits):
                hits.append((u, v, s, p))
    hits.sort(key=lambda hit: hit[2])
    return hits


def brep_faces(geometry) -> list[AtomicSurface]:
    if isinstance(geometry, AtomicSurface):
        return [geometry]
    if isinstance(geometry, AtomicTrimmedSurface):
        return [geometry.surface]
    if isinstance(geometry, AtomicBrep):
        faces: list[AtomicSurface] = []
        for face in geometry.faces:
            faces.extend(brep_faces(face))
        return faces
    if isinstance(geometry, AtomicBox):
        from pyhopper.Utils.Boxes import box_to_brep

        return brep_faces(box_to_brep(geometry))
    return []


def brep_closest_point(geometry, point: AtomicPoint) -> tuple[AtomicPoint, AtomicVector, float]:
    """Closest point over the faces of a brep (or surface / box) with the unit normal there."""
    from pyhopper.Utils.Nurbs import surface_normal

    best = None
    for face in brep_faces(geometry):
        u, v, p, d, _ = surface_closest_point(face, point)
        if best is None or d < best[2] - 1e-15:
            best = (p, surface_normal(face, u, v), d)
    if best is None:
        raise TypeError(f"{type(geometry).__name__} has no surface faces")
    return best


# ── geometry lists (Pull Point, Project Point, Curve Nearest Object) ───────────


def geometry_closest_point(geometry, point: AtomicPoint) -> tuple[AtomicPoint, float]:
    """Closest point on any geometry item: points, curves, surfaces, breps, boxes and planes."""
    if isinstance(geometry, AtomicPoint):
        return geometry, distance(geometry, point)
    if isinstance(geometry, CURVE_TYPES):
        _, p, d = curve_closest_point(geometry, point)
        return p, d
    if isinstance(geometry, AtomicPlane):
        p = project_point(geometry, point)
        return p, distance(p, point)
    faces = brep_faces(geometry)
    if faces:
        p, _, d = brep_closest_point(geometry, point)
        return p, d
    raise TypeError(f"Cannot find a closest point on {type(geometry).__name__}")


def geometry_ray_hit(geometry, origin: AtomicPoint, direction: AtomicVector, tolerance: float = ABSOLUTE_TOLERANCE) -> tuple[float, AtomicPoint] | None:
    """First point where the ray ``origin + s·direction`` (``s >= 0``) meets the geometry: surfaces
    and breps exactly, curves and points where the ray passes within *tolerance* (the point on the
    ray, as Grasshopper reports it). ``None`` when the ray misses."""
    axis = unit(direction)
    faces = brep_faces(geometry)
    if faces:
        hits = [hit for face in faces for hit in surface_line_hits(face, origin, axis) if hit[2] >= -1e-9]
        if not hits:
            return None
        hit = min(hits, key=lambda item: item[2])
        return hit[2], hit[3]
    if isinstance(geometry, AtomicPoint):
        s = dot(sub(geometry, origin), axis)
        on_ray = AtomicPoint(origin.x + axis.x * s, origin.y + axis.y * s, origin.z + axis.z * s)
        return (s, on_ray) if s >= -1e-9 and distance(on_ray, geometry) <= tolerance else None
    if isinstance(geometry, CURVE_TYPES):
        _, s, _, on_ray, d = curve_line_closest(geometry, origin, axis)
        return (s, on_ray) if s >= -1e-9 and d <= tolerance else None
    if isinstance(geometry, AtomicPlane):
        denominator = dot(geometry.normal, axis)
        if abs(denominator) <= _ZERO:
            return None
        s = dot(sub(geometry.origin, origin), geometry.normal) / denominator
        return (s, AtomicPoint(origin.x + axis.x * s, origin.y + axis.y * s, origin.z + axis.z * s)) if s >= -1e-9 else None
    raise TypeError(f"Cannot project onto {type(geometry).__name__}")


def curve_geometry_closest(curve, geometry) -> tuple[AtomicPoint, AtomicPoint, float]:
    """Closest pair between a curve and another geometry item: ``(point on curve, point on geometry, distance)``."""
    if isinstance(geometry, AtomicPoint):
        _, p, d = curve_closest_point(curve, geometry)
        return p, geometry, d
    if isinstance(geometry, CURVE_TYPES):
        _, _, pa, pb, d = curve_curve_closest(curve, geometry)
        return pa, pb, d
    if isinstance(geometry, AtomicPlane):
        # the curve point nearest the plane: extreme along the normal towards the plane
        start, end = curve_domain_of(curve)
        best = None
        for t in _height_candidates(curve, geometry):
            p = curve_point_at(curve, t)
            q = project_point(geometry, p)
            d = distance(p, q)
            if best is None or d < best[2] - _ZERO:
                best = (p, q, d)
        return best
    faces = brep_faces(geometry)
    if not faces:
        raise TypeError(f"Cannot measure a curve against {type(geometry).__name__}")
    a0, a1 = curve_domain_of(curve)
    samples = 48
    best = None
    for i in range(samples + 1):
        t = a0 + (a1 - a0) * i / samples
        p = curve_point_at(curve, t)
        q, _, d = brep_closest_point(geometry, p)
        if best is None or d < best[3]:
            best = (t, p, q, d)
    t, p, q, d = best
    for _ in range(60):
        t_new, p_new, _ = curve_closest_point(curve, q)
        q_new, _, d_new = brep_closest_point(geometry, p_new)
        converged = abs(t_new - t) <= 1e-13 * max(1.0, abs(a1 - a0))
        t, p, q, d = t_new, p_new, q_new, d_new
        if converged:
            break
    return p, q, d


# ── planar relationships ───────────────────────────────────────────


def _canonical_plane(plane: AtomicPlane) -> AtomicPlane:
    """Rhino's fitted planes for polylines and NURBS curves come with a canonical normal: flipped so
    the normal points towards +z (then +y, then +x)."""
    n = plane.normal
    flip = n.z < -_ZERO or (abs(n.z) <= _ZERO and (n.y < -_ZERO or (abs(n.y) <= _ZERO and n.x < 0)))
    if not flip:
        return plane
    return AtomicPlane(plane.origin, AtomicVector(-n.x, -n.y, -n.z), plane.x_axis)


def curve_reference_plane(curve) -> AtomicPlane:
    """The plane Grasshopper's Curve Side falls back to: arcs and circles use their own plane, other
    planar curves a fitted plane with a canonical normal, lines and non-planar curves World XY."""
    if isinstance(curve, (AtomicArc, AtomicCircle, AtomicRectangle)):
        return curve.plane
    if isinstance(curve, AtomicLine):
        return AtomicPlane.world_xy()
    plane, deviation = curve_planarity(curve)
    if deviation > 1e-9:
        return AtomicPlane.world_xy()
    return _canonical_plane(plane)


def curve_side(curve, point: AtomicPoint, plane: AtomicPlane | None) -> int:
    """-1 when the point lies left of the curve seen from the plane's normal, +1 right, 0 within the
    absolute tolerance of the curve (Grasshopper's Curve Side)."""
    reference = plane if plane is not None else curve_reference_plane(curve)
    t, closest, d = curve_closest_point(curve, point)
    tangent = curve_tangent_at(curve, t)
    offset = sub(point, closest)
    side = dot(cross(tangent, offset), reference.normal)
    if d <= ABSOLUTE_TOLERANCE or abs(side) <= 1e-9 * max(1.0, length(offset)):
        return 0
    return -1 if side > 0 else 1


def _polygon_contains(polygon: list[tuple[float, float]], x: float, y: float) -> bool:
    inside = False
    count = len(polygon)
    for i in range(count):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % count]
        if (y1 > y) != (y2 > y):
            cross_x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < cross_x:
                inside = not inside
    return inside


def point_in_closed_curve(curve, point: AtomicPoint, tolerance: float = ABSOLUTE_TOLERANCE) -> tuple[int, AtomicPoint]:
    """Grasshopper's Point In Curve: ``(relationship, point projected onto the curve plane)`` with
    0 outside, 1 coincident (within *tolerance*), 2 inside. Raises for open or non-planar curves."""
    if not curve_is_closed(curve):
        raise ValueError("Curve Point relationship cannot be determined.")
    plane, deviation = curve_planarity(curve)
    if isinstance(curve, (AtomicArc, AtomicCircle, AtomicRectangle)):
        plane = curve.plane
    elif deviation > 1e-9:
        raise ValueError("Curve Point relationship cannot be determined.")
    projected = project_point(plane, point)
    _, closest, d = curve_closest_point(curve, projected)
    if d <= tolerance:
        return 1, projected
    from pyhopper.Utils.CurveFitting import curve_to_polyline

    polyline = curve if isinstance(curve, AtomicPolyline) else curve_to_polyline(curve, 1e-6)
    polygon = [plane_coordinates(plane, p)[:2] for p in polyline.points]
    x, y, _ = plane_coordinates(plane, projected)
    return (2 if _polygon_contains(polygon, x, y) else 0), projected


def _height_candidates(curve, plane: AtomicPlane) -> list[float]:
    """Parameters where the height above *plane* is stationary, plus the curve ends."""
    start, end = curve_domain_of(curve)
    candidates = [start, end]
    if isinstance(curve, (AtomicLine,)):
        return candidates
    if isinstance(curve, (AtomicPolyline, AtomicRectangle)):
        count = len(curve.points) - 1 if isinstance(curve, AtomicPolyline) else 4
        return candidates + [i / count for i in range(1, count)]
    if isinstance(curve, AtomicPolyCurve):
        breaks = polycurve_breaks(curve)
        for index, segment in enumerate(curve.segments):
            seg_start, seg_end = curve_domain_of(segment)
            for t in _height_candidates(segment, plane):
                local = 0.0 if seg_end - seg_start <= _ZERO else (t - seg_start) / (seg_end - seg_start)
                candidates.append(breaks[index] + (breaks[index + 1] - breaks[index]) * local)
        return sorted(set(candidates))
    normal = plane.normal
    samples = 64
    heights = []
    for i in range(samples + 1):
        t = start + (end - start) * i / samples
        _, first, _, _ = curve_derivatives_at(curve, t)
        heights.append((t, dot(first, normal)))
    for (t0, h0), (t1, h1) in zip(heights, heights[1:]):
        if h0 == 0.0:
            candidates.append(t0)
        if h0 * h1 < 0.0:
            lo, hi = t0, t1
            for _ in range(80):  # bisection on the height derivative
                mid = 0.5 * (lo + hi)
                _, first, _, _ = curve_derivatives_at(curve, mid)
                if dot(first, normal) * h0 > 0:
                    lo = mid
                else:
                    hi = mid
            candidates.append(0.5 * (lo + hi))
    return candidates


def curve_extremes(curve, plane: AtomicPlane) -> tuple[AtomicPoint, AtomicPoint]:
    """Highest and lowest points of the curve measured along the plane's normal (ties go to the
    earliest parameter)."""
    normal = unit(plane.normal)
    best_high = best_low = None
    for t in sorted(_height_candidates(curve, plane)):
        p = curve_point_at(curve, t)
        h = dot(sub(p, plane.origin), normal)
        if best_high is None or h > best_high[0] + 1e-12:
            best_high = (h, p)
        if best_low is None or h < best_low[0] - 1e-12:
            best_low = (h, p)
    return best_high[1], best_low[1]


def uv_in_trim(surface, u: float, v: float) -> bool:
    """Whether a (u, v) parameter lies on the surface: inside the domain for an untrimmed surface,
    inside the outer loop and outside the holes (loops live in parameter space) for a trimmed one;
    edges count as inside."""
    base = surface.surface if isinstance(surface, AtomicTrimmedSurface) else surface
    (u0, u1), (v0, v1) = surface_domain(base)
    tolerance = 1e-9
    if not (u0 - tolerance <= u <= u1 + tolerance and v0 - tolerance <= v <= v1 + tolerance):
        return False
    if not isinstance(surface, AtomicTrimmedSurface):
        return True
    probe = AtomicPoint(u, v, 0.0)
    loops = [surface.outer, *surface.holes]
    for index, loop in enumerate(loops):
        _, _, d = curve_closest_point(loop, probe)
        if d <= tolerance:
            return True  # on an edge
        contained = _polygon_contains([(p.x, p.y) for p in loop.points], u, v)
        if index == 0 and not contained:
            return False
        if index > 0 and contained:
            return False
    return True
