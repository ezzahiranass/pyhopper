"""Rhino-style curve interpolation for the Curve > Spline components.

Rhino's ``CreateInterpolatedCurve`` builds a clamped cubic with ``n + 2`` control
points and knots at the interpolation parameters; the second and penultimate
control points sit a third of the first/last chord along the end tangents (the
user's, or the derivative of the parabola through the three end points when none
is given). Everything here was read off Grasshopper 8 and is reproduced exactly.
"""

from __future__ import annotations

import math
from typing import Sequence

from pyhopper.Core.Atoms import AtomicNurbsCurve, AtomicPoint, AtomicVector
from pyhopper.Utils.Nurbs import basis_row, solve_linear_system
from pyhopper.Utils.Vectors import angle, distance, is_zero, sub, unit

UNIFORM, CHORD, SQRT_CHORD = 0, 1, 2


def interpolation_parameters(points: Sequence[AtomicPoint], knot_style: int) -> list[float]:
    """Rhino's parameters: 0, 1, 2 … (uniform), cumulative chord lengths, or cumulative square roots."""
    if knot_style not in (UNIFORM, CHORD, SQRT_CHORD):
        raise ValueError("knot style must be 0 (uniform), 1 (chord) or 2 (square-root chord)")
    parameters = [0.0]
    for a, b in zip(points, points[1:]):
        step = 1.0 if knot_style == UNIFORM else distance(a, b) if knot_style == CHORD else math.sqrt(distance(a, b))
        if step <= 0.0:
            raise ValueError("interpolation needs distinct consecutive points")
        parameters.append(parameters[-1] + step)
    return parameters


def parabola_end_direction(points: Sequence[AtomicPoint], parameters: Sequence[float], *, at_start: bool) -> AtomicVector:
    """Direction of the Lagrange parabola through the three end points at the end point (Rhino's
    estimate for a missing end tangent)."""
    if len(points) < 3:
        return unit(sub(points[1], points[0]) if at_start else sub(points[-1], points[-2]))
    trio = (points[0], points[1], points[2]) if at_start else (points[-3], points[-2], points[-1])
    t = (parameters[0], parameters[1], parameters[2]) if at_start else (parameters[-3], parameters[-2], parameters[-1])
    u = t[0] if at_start else t[2]
    coefficients = []
    for i in range(3):
        j, k = [m for m in range(3) if m != i]
        coefficients.append(((u - t[j]) + (u - t[k])) / ((t[i] - t[j]) * (t[i] - t[k])))
    return unit(AtomicVector(*(sum(c * getattr(p, axis) for c, p in zip(coefficients, trio)) for axis in "xyz")))


def rhino_interpolated_curve(points: Sequence[AtomicPoint], knot_style: int = CHORD, start_tangent: AtomicVector | None = None, end_tangent: AtomicVector | None = None) -> AtomicNurbsCurve:
    """Degree-3 interpolation through ``points`` exactly as Rhino builds it (see the module docstring).
    Zero or missing tangents are estimated; two points give a single cubic Bezier whose tangent
    handles follow the circular-arc rule Rhino uses for a single span."""
    pts = [p for p in points]
    if len(pts) < 2:
        raise ValueError("interpolation needs at least two points")
    if not all(isinstance(p, AtomicPoint) for p in pts):
        raise TypeError("interpolation points must be AtomicPoint values")
    t0 = None if start_tangent is None or is_zero(start_tangent) else unit(start_tangent)
    t1 = None if end_tangent is None or is_zero(end_tangent) else unit(end_tangent)
    parameters = interpolation_parameters(pts, knot_style)
    n = len(pts)
    if n == 2:
        return _single_span(pts[0], pts[1], t0, t1, parameters[-1])
    # Rhino estimates missing tangents from chord-length parabolas whatever the knot style
    chord_parameters = parameters if knot_style == CHORD else interpolation_parameters(pts, CHORD)
    d0 = t0 if t0 is not None else parabola_end_direction(pts, chord_parameters, at_start=True)
    d1 = t1 if t1 is not None else parabola_end_direction(pts, chord_parameters, at_start=False)
    first, last = distance(pts[0], pts[1]) / 3.0, distance(pts[-1], pts[-2]) / 3.0
    cp1 = AtomicPoint(pts[0].x + first * d0.x, pts[0].y + first * d0.y, pts[0].z + first * d0.z)
    cpn = AtomicPoint(pts[-1].x - last * d1.x, pts[-1].y - last * d1.y, pts[-1].z - last * d1.z)
    knots = tuple([parameters[0]] * 4 + parameters[1:-1] + [parameters[-1]] * 4)
    count = n + 2
    # unknown interior control points 2 .. n-1 from the interior interpolation conditions
    rows, rhs = [], []
    known = {0: pts[0], 1: cp1, count - 2: cpn, count - 1: pts[-1]}
    unknown = [i for i in range(count) if i not in known]
    for t, p in zip(parameters[1:-1], pts[1:-1]):
        basis = basis_row(t, 3, knots, count)
        rows.append([basis[i] for i in unknown])
        rhs.append([getattr(p, axis) - sum(basis[i] * getattr(known[i], axis) for i in known) for axis in "xyz"])
    solved = solve_linear_system(rows, rhs) if unknown else []
    controls = []
    cursor = 0
    for i in range(count):
        if i in known:
            controls.append(known[i])
        else:
            controls.append(AtomicPoint(*solved[cursor]))
            cursor += 1
    return AtomicNurbsCurve(tuple(controls), tuple(1.0 for _ in controls), knots, 3)


def _single_span(a: AtomicPoint, b: AtomicPoint, t0: AtomicVector | None, t1: AtomicVector | None, span: float) -> AtomicNurbsCurve:
    chord = sub(b, a)
    length = distance(a, b)
    direction = unit(chord)

    def handle(tangent: AtomicVector | None, towards: AtomicVector) -> float:
        if tangent is None:
            return length / 3.0
        theta = 2.0 * angle(tangent, towards)  # arc through both points tangent to ``tangent``
        if theta <= 1e-12:
            return length / 3.0
        radius = length / (2.0 * math.sin(theta / 2.0))
        return (4.0 / 3.0) * math.tan(theta / 4.0) * radius

    d0 = t0 if t0 is not None else direction
    d1 = t1 if t1 is not None else direction
    h0, h1 = handle(t0, direction), handle(t1, direction)
    cp1 = AtomicPoint(a.x + h0 * d0.x, a.y + h0 * d0.y, a.z + h0 * d0.z)
    cp2 = AtomicPoint(b.x - h1 * d1.x, b.y - h1 * d1.y, b.z - h1 * d1.z)
    return AtomicNurbsCurve((a, cp1, cp2, b), (1.0, 1.0, 1.0, 1.0), (0.0, 0.0, 0.0, 0.0, span, span, span, span), 3)


def kinky_curve(points: Sequence[AtomicPoint], degree: int, kink_angle: float) -> AtomicNurbsCurve:
    """Grasshopper's Kinky Curve: vertices where consecutive segments turn by more than ``kink_angle``
    become kinks; runs of two vertices are lines (knot span = length), longer runs are interpolated
    with uniform knots (degree 1: the polyline; degree 3: Rhino's interpolation), and the pieces are
    joined with full-multiplicity knots, lines being raised to the curve degree when needed."""
    pts = list(points)
    if len(pts) < 2:
        raise ValueError("Kinky Curve needs at least two vertices")
    if not all(isinstance(p, AtomicPoint) for p in pts):
        raise TypeError("Kinky Curve vertices must be AtomicPoint values")
    if int(degree) not in (1, 3):
        raise ValueError("Kinky Curve interpolates with degree 1 or 3 in pyhopper")
    threshold = float(kink_angle)
    kinks = [0] + [i for i in range(1, len(pts) - 1) if angle(sub(pts[i], pts[i - 1]), sub(pts[i + 1], pts[i])) > threshold + 1e-12] + [len(pts) - 1]
    runs = [pts[start:end + 1] for start, end in zip(kinks, kinks[1:])]
    curve_degree = int(degree) if any(len(run) > 2 for run in runs) else 1
    controls: list[AtomicPoint] = []
    knots: list[float] = []
    offset = 0.0
    for run in runs:
        if len(run) == 2:
            span = distance(run[0], run[1])
            if curve_degree == 1:
                piece_controls, piece_knots = [run[0], run[1]], [0.0, 0.0, span, span]
            else:
                piece_controls = [run[0], _lerp(run[0], run[1], 1.0 / 3.0), _lerp(run[0], run[1], 2.0 / 3.0), run[1]]
                piece_knots = [0.0] * 4 + [span] * 4
        elif curve_degree == 1:
            piece_controls = list(run)
            piece_knots = [0.0, 0.0] + [float(i) for i in range(1, len(run) - 1)] + [float(len(run) - 1)] * 2
        else:
            piece = rhino_interpolated_curve(run, UNIFORM)
            piece_controls, piece_knots = list(piece.control_points), list(piece.knots)
        if controls:
            piece_controls = piece_controls[1:]  # shared joint
            piece_knots = piece_knots[curve_degree + 1:]
            knots.pop()  # the joint knot keeps multiplicity ``degree`` (a C0 join)
        controls.extend(piece_controls)
        knots.extend(offset + k for k in piece_knots)
        offset = knots[-1]
    return AtomicNurbsCurve(tuple(controls), tuple(1.0 for _ in controls), tuple(knots), curve_degree)


def _lerp(a: AtomicPoint, b: AtomicPoint, t: float) -> AtomicPoint:
    return AtomicPoint(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t)
