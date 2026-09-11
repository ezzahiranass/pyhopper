"""Arc construction with Grasshopper's conventions (verified against Grasshopper 8).

* ``arc_from_plane`` normalises a descending angle domain the way Grasshopper
  does: the plane's normal flips and the angles negate, so the arc keeps its
  geometry and runs counter-clockwise about the new normal.
* ``arc_from_three_points`` puts the plane origin at the centre with X towards
  the first point; the normal follows the turning direction A -> B -> C.
* ``arc_from_start_end_direction`` fits the arc tangent to ``direction`` at the
  start; X points at the start.

Degenerate inputs (collinear points, a direction along the chord, a zero
direction) yield a line and an infinite radius, exactly like Grasshopper.
"""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicArc, AtomicInterval, AtomicLine, AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Utils.Vectors import add, cross, dot, is_zero, perpendicular, scale, sub, translate, unit

_TOLERANCE = 1e-12


def arc_length(arc: AtomicArc) -> float:
    return abs(float(arc.radius) * float(arc.angle.length))


def arc_from_plane(plane: AtomicPlane, radius: float, angle: AtomicInterval) -> AtomicArc:
    """Arc on ``plane`` over ``angle`` (radians); a reversed domain flips the plane like Grasshopper."""
    start, end = float(angle.start), float(angle.end)
    if end < start:
        flipped = AtomicPlane(origin=plane.origin, normal=AtomicVector(-plane.normal.x, -plane.normal.y, -plane.normal.z), x_axis=plane.x_axis)
        return AtomicArc(flipped, float(radius), AtomicInterval(-start, -end))
    return AtomicArc(plane, float(radius), AtomicInterval(start, end))


def _degenerate(a: AtomicPoint, b: AtomicPoint) -> tuple[AtomicLine, AtomicPlane, float]:
    """Grasshopper's answer when no proper arc exists: the chord as a line, radius infinity."""
    x_axis = unit(sub(b, a)) if not is_zero(sub(b, a)) else AtomicVector.unit_x()
    normal = cross(x_axis, perpendicular(x_axis))
    return AtomicLine(a, b), AtomicPlane(origin=a, normal=unit(normal), x_axis=x_axis), math.inf


def _sweep(plane: AtomicPlane, point: AtomicPoint) -> float:
    """Counter-clockwise angle (0 <= a < 2pi) of ``point`` about the plane normal from its X axis."""
    offset = sub(point, plane.origin)
    angle = math.atan2(dot(offset, plane.y_axis), dot(offset, plane.x_axis))
    return angle + 2.0 * math.pi if angle < 0.0 else angle


def arc_from_three_points(a: AtomicPoint, b: AtomicPoint, c: AtomicPoint) -> tuple[AtomicArc | AtomicLine, AtomicPlane, float]:
    """(arc, plane, radius) through A, B, C — or (line A-C, plane, inf) when they are collinear."""
    ab = sub(b, a)
    ac = sub(c, a)
    normal = cross(ab, ac)
    scale_reference = max(1.0, dot(ab, ab), dot(ac, ac))
    if dot(normal, normal) <= _TOLERANCE * scale_reference * scale_reference:
        return _degenerate(a, c)
    # circumcentre: a + (|ac|^2 (n x ab) + |ab|^2 (ac x n)) / (2 |n|^2)
    offset = scale(add(scale(cross(normal, ab), dot(ac, ac)), scale(cross(ac, normal), dot(ab, ab))), 1.0 / (2.0 * dot(normal, normal)))
    centre = translate(a, offset)
    radius = math.sqrt(dot(sub(a, centre), sub(a, centre)))
    plane = AtomicPlane(origin=centre, normal=unit(normal), x_axis=unit(sub(a, centre)))
    sweep = _sweep(plane, c)
    return AtomicArc(plane, radius, AtomicInterval(0.0, sweep)), plane, radius


def arc_from_start_end_direction(start: AtomicPoint, end: AtomicPoint, direction: AtomicVector) -> tuple[AtomicArc | AtomicLine, AtomicPlane, float]:
    """(arc, plane, radius) from start to end, tangent to ``direction`` at the start."""
    chord = sub(end, start)
    normal = cross(direction, chord)
    scale_reference = max(1.0, dot(chord, chord), dot(direction, direction))
    if is_zero(direction) or dot(normal, normal) <= _TOLERANCE * scale_reference * scale_reference:
        return _degenerate(start, end)
    unit_normal = unit(normal)
    left = unit(cross(unit_normal, unit(direction)))  # in-plane, perpendicular to the tangent, towards the end point
    radius = dot(chord, chord) / (2.0 * dot(left, chord))
    centre = AtomicPoint(start.x + left.x * radius, start.y + left.y * radius, start.z + left.z * radius)
    plane = AtomicPlane(origin=centre, normal=unit_normal, x_axis=unit(sub(start, centre)))
    return AtomicArc(plane, radius, AtomicInterval(0.0, _sweep(plane, end))), plane, radius
