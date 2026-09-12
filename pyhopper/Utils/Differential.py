"""Differential geometry for the K1 analysis components: curvature, torsion and
Frenet frames of curves, curve discontinuities, surface curvatures and
osculating circles, all with the conventions read off Grasshopper 8.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from pyhopper.Core.Atoms import AtomicArc, AtomicCircle, AtomicEllipse, AtomicLine, AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicSurface, AtomicVector
from pyhopper.Utils.Curves import curve_derivatives_at, curve_domain_of, curve_is_closed, curve_point_at
from pyhopper.Utils.Nurbs import surface_derivatives, surface_domain, surface_normal
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Utils.Vectors import cross, dot, is_zero, length, perpendicular, scale, sub, unit

_TOLERANCE = 1e-9
INFINITE_CURVE_LINE = 100.0  # Grasshopper draws a 200-long tangent line where a curvature circle is infinite
INFINITE_SURFACE_LINE = 5.0  # and a 10-long one for a flat osculating circle


# ── curves ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CurveAnalysis:
    point: AtomicPoint
    first: AtomicVector
    second: AtomicVector
    third: AtomicVector
    tangent: AtomicVector
    curvature: float
    curvature_vector: AtomicVector


def curve_analysis(curve, parameter: float) -> CurveAnalysis:
    """Point, first three derivatives, unit tangent and curvature of any curve atom at its native parameter."""
    point, first, second, third = curve_derivatives_at(curve, float(parameter))
    speed_squared = dot(first, first)
    if speed_squared <= _TOLERANCE:
        raise ValueError("Cannot analyse a stationary curve point")
    tangent = unit(first)
    normal_component = sub(second, scale(first, dot(first, second) / speed_squared))
    curvature_vector = scale(normal_component, 1.0 / speed_squared)  # k n
    return CurveAnalysis(point, first, second, third, tangent, length(curvature_vector), curvature_vector)


def curvature_circle(analysis: CurveAnalysis):
    """Osculating circle (plane at the centre, x axis towards the point, normal along the binormal);
    a straight stretch gives Grasshopper's 200-long tangent line instead."""
    if analysis.curvature <= _TOLERANCE:
        p, t = analysis.point, analysis.tangent
        return AtomicLine(AtomicPoint(p.x - INFINITE_CURVE_LINE * t.x, p.y - INFINITE_CURVE_LINE * t.y, p.z - INFINITE_CURVE_LINE * t.z),
                          AtomicPoint(p.x + INFINITE_CURVE_LINE * t.x, p.y + INFINITE_CURVE_LINE * t.y, p.z + INFINITE_CURVE_LINE * t.z))
    radius = 1.0 / analysis.curvature
    normal = unit(analysis.curvature_vector)
    centre = AtomicPoint(analysis.point.x + normal.x * radius, analysis.point.y + normal.y * radius, analysis.point.z + normal.z * radius)
    binormal = unit(cross(analysis.tangent, normal))
    return AtomicCircle(AtomicPlane(centre, binormal, AtomicVector(-normal.x, -normal.y, -normal.z)), radius)


def frenet_frame(analysis: CurveAnalysis) -> AtomicPlane:
    """Rhino's curve frame: x along the tangent, y towards the centre of curvature (openNURBS'
    perpendicular of the tangent where the curvature vanishes), z the binormal."""
    normal = unit(analysis.curvature_vector) if analysis.curvature > _TOLERANCE else perpendicular(analysis.tangent)
    return AtomicPlane(analysis.point, unit(cross(analysis.tangent, normal)), analysis.tangent)


def torsion(analysis: CurveAnalysis) -> float:
    """Frenet torsion ((r' × r'') · r''') / |r' × r''|²; zero on straight stretches."""
    binormal = cross(analysis.first, analysis.second)
    denominator = dot(binormal, binormal)
    if denominator <= _TOLERANCE:
        return 0.0
    return dot(binormal, analysis.third) / denominator


def _interior_knots(nurbs: AtomicNurbsCurve) -> list[float]:
    start, end = nurbs.knots[nurbs.degree], nurbs.knots[len(nurbs.control_points)]
    seen, knots = set(), []
    for knot in nurbs.knots[nurbs.degree + 1: len(nurbs.control_points)]:
        if start + _TOLERANCE < knot < end - _TOLERANCE and knot not in seen:
            seen.add(knot)
            knots.append(knot)
    return knots


def _jumps(before: CurveAnalysis, after: CurveAnalysis, level: int) -> bool:
    """True when the tangent direction (level 1) or also the curvature vector (level 2) differs."""
    if length(sub(before.tangent, after.tangent)) > 1e-5:
        return True
    return level >= 2 and length(sub(before.curvature_vector, after.curvature_vector)) > 1e-5 * max(1.0, before.curvature, after.curvature)


def discontinuities(curve, level: int) -> tuple[list[AtomicPoint], list[float]]:
    """Grasshopper's Discontinuity: the ends of an open curve plus every interior parameter where the
    curve is not C1 (level 1, tangent direction), not C2 (level 2, adds curvature jumps) or not C∞
    (level 3, every interior knot or polyline vertex); the seam of a closed curve counts once, at the
    start. Circles, arcs and ellipses are smooth everywhere."""
    level = int(level)
    if level not in (1, 2, 3):
        raise ValueError("Discontinuity level must be 1 (C1), 2 (C2) or 3 (C-infinite)")
    start, end = curve_domain_of(curve)
    closed = curve_is_closed(curve)
    parameters: list[float] = []
    if not closed:
        parameters.append(start)
    if not isinstance(curve, (AtomicCircle, AtomicArc, AtomicEllipse)):
        nurbs = as_nurbs_curve(curve)  # shares the atom's parameterisation
        span = end - start
        step = max(span * 1e-7, 1e-12)
        if closed and (level == 3 or _jumps(curve_analysis(nurbs, end - step), curve_analysis(nurbs, start + step), level)):
            parameters.append(start)
        for knot in _interior_knots(nurbs):
            if level == 3 or _jumps(curve_analysis(nurbs, knot - step), curve_analysis(nurbs, knot + step), level):
                parameters.append(knot)
    if not closed:
        parameters.append(end)
    return [curve_point_at(curve, t) for t in parameters], parameters


# ── surfaces ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class SurfaceAnalysis:
    point: AtomicPoint
    normal: AtomicVector
    u_direction: AtomicVector
    v_direction: AtomicVector
    gaussian: float
    mean: float
    maximum: float
    minimum: float
    max_direction: AtomicVector
    min_direction: AtomicVector

    @property
    def frame(self) -> AtomicPlane:
        return AtomicPlane(self.point, self.normal, self.u_direction)


def surface_analysis(surface: AtomicSurface, u: float, v: float) -> SurfaceAnalysis:
    """Point, unit normal (Su × Sv), unit U/V directions, Gaussian and mean curvature and the principal
    curvatures with their directions ("maximum" is the larger absolute curvature, ties going to the
    algebraically larger one, like Grasshopper)."""
    ders = surface_derivatives(surface, float(u), float(v), 2)
    su, sv = ders.du, ders.dv
    normal_raw = cross(su, sv)
    if is_zero(normal_raw, 1e-14):
        raise ValueError("The surface normal is undefined at this parameter (degenerate derivatives)")
    normal = unit(normal_raw)
    e, f, g = dot(su, su), dot(su, sv), dot(sv, sv)
    l, m, n = dot(ders.duu, normal), dot(ders.duv, normal), dot(ders.dvv, normal)
    denominator = e * g - f * f
    gaussian = (l * n - m * m) / denominator
    mean = (e * n - 2.0 * f * m + g * l) / (2.0 * denominator)
    root = math.sqrt(max(mean * mean - gaussian, 0.0))
    k1, k2 = mean + root, mean - root
    if root <= 1e-9 * max(1.0, abs(mean)):
        d1, d2 = unit(su), unit(cross(normal, unit(su)))
    else:
        d1, d2 = _principal_direction(k1, su, sv, e, f, g, l, m, n), _principal_direction(k2, su, sv, e, f, g, l, m, n)
    if abs(k2) > abs(k1) + 1e-12:
        k1, k2, d1, d2 = k2, k1, d2, d1
    return SurfaceAnalysis(ders.point, normal, unit(su), unit(sv), gaussian, mean, k1, k2, d1, d2)


def _principal_direction(kappa, su, sv, e, f, g, l, m, n) -> AtomicVector:
    rows = ((l - kappa * e, m - kappa * f), (m - kappa * f, n - kappa * g))
    row = max(rows, key=lambda r: r[0] * r[0] + r[1] * r[1])
    a, b = -row[1], row[0]
    if abs(a) + abs(b) <= 1e-14:
        return unit(su)
    return unit(AtomicVector(a * su.x + b * sv.x, a * su.y + b * sv.y, a * su.z + b * sv.z))


def osculating_circle(analysis: SurfaceAnalysis, kappa: float, direction: AtomicVector):
    """Circle of radius 1/|κ| in the plane spanned by the principal direction and the normal (plane x
    along the direction, normal = direction × surface normal); a flat direction gives Grasshopper's
    10-long line through the point instead."""
    p, nrm = analysis.point, analysis.normal
    if abs(kappa) <= _TOLERANCE:
        return AtomicLine(AtomicPoint(p.x - INFINITE_SURFACE_LINE * direction.x, p.y - INFINITE_SURFACE_LINE * direction.y, p.z - INFINITE_SURFACE_LINE * direction.z),
                          AtomicPoint(p.x + INFINITE_SURFACE_LINE * direction.x, p.y + INFINITE_SURFACE_LINE * direction.y, p.z + INFINITE_SURFACE_LINE * direction.z))
    radius = 1.0 / kappa
    centre = AtomicPoint(p.x + nrm.x * radius, p.y + nrm.y * radius, p.z + nrm.z * radius)
    return AtomicCircle(AtomicPlane(centre, unit(cross(direction, nrm)), direction), abs(radius))


def surface_grid_parameters(surface: AtomicSurface, u_count: int, v_count: int) -> tuple[list[float], list[float]]:
    (u0, u1), (v0, v1) = surface_domain(surface)
    return [u0 + (u1 - u0) * i / u_count for i in range(u_count + 1)], [v0 + (v1 - v0) * j / v_count for j in range(v_count + 1)]


def offset_surface(surface: AtomicSurface, distance: float) -> AtomicSurface:
    """Offset along the normals: planar surfaces translate exactly; others are approximated by
    interpolating a dense grid of offset points on the original domain (Rhino refits too, differently)."""
    from pyhopper.Utils.SurfaceBuilders import redomain_surface, surface_from_grid

    us, vs = surface_grid_parameters(surface, 2, 2)
    normals = [surface_normal(surface, u, v) for u in us for v in vs]
    if all(length(sub(normal, normals[0])) <= 1e-9 for normal in normals):
        step = scale(normals[0], float(distance))
        rows = tuple(tuple(AtomicPoint(p.x + step.x, p.y + step.y, p.z + step.z) for p in row) for row in surface.poles)
        return AtomicSurface(rows, surface.weights, surface.u_knots, surface.v_knots, surface.u_mults, surface.v_mults, surface.u_degree, surface.v_degree, surface.u_periodic, surface.v_periodic)
    u_samples = max(2 * len(surface.poles[0]) + 1, 5)
    v_samples = max(2 * len(surface.poles) + 1, 5)
    us, vs = surface_grid_parameters(surface, u_samples - 1, v_samples - 1)
    grid = []
    for v in vs:
        row = []
        for u in us:
            ders = surface_derivatives(surface, u, v, 1)
            normal = unit(cross(ders.du, ders.dv))
            row.append(AtomicPoint(ders.point.x + normal.x * distance, ders.point.y + normal.y * distance, ders.point.z + normal.z * distance))
        grid.append(row)
    return redomain_surface(surface_from_grid(grid, interpolate=True), *surface_domain(surface))
