"""Perpendicular frames along curves (Grasshopper Perp Frames / Rhino perpendicular frames).

Two constructions, both verified against Grasshopper 8:

* ``perpendicular_frame`` — the frame Rhino builds from a point and a tangent
  alone (``Plane(origin, normal)``): Z is the tangent, X is
  ``Vectors.perpendicular(tangent)`` (openNURBS ``PerpendicularTo``). This is
  what Perp Frames emits with ``align = False``.
* ``rotation_minimizing_frames`` — Rhino's ``Curve.GetPerpendicularFrames``:
  the first frame's X is the curvature direction (or, on a straight, world Z
  projected perpendicular to the tangent, then world X), and every following
  frame is carried along with the double-reflection method of Wang et al.
  (2008) over the requested samples only. Coarse samples twist a little, and so
  does Grasshopper's — the results match to floating-point precision.
"""

from __future__ import annotations

from typing import Sequence

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Utils.Planes import plane_from_normal
from pyhopper.Utils.Vectors import dot, is_zero, scale, sub, unit

_STRAIGHT = 1e-9


def perpendicular_frame(point: AtomicPoint, tangent: AtomicVector) -> AtomicPlane:
    """Frame with Z along the tangent and Rhino's default X axis."""
    return plane_from_normal(point, tangent)


def initial_frame_axis(tangent: AtomicVector, curvature: AtomicVector | None = None) -> AtomicVector:
    """X axis Rhino starts a perpendicular-frame sweep with.

    The curvature direction when the curve bends; otherwise world Z (then X,
    then Y) projected onto the plane perpendicular to the tangent.
    """
    direction = unit(tangent)
    if curvature is not None and not is_zero(curvature, _STRAIGHT):
        return unit(_reject(curvature, direction))
    for candidate in (AtomicVector.unit_z(), AtomicVector.unit_x(), AtomicVector.unit_y()):
        projected = _reject(candidate, direction)
        if not is_zero(projected, _STRAIGHT):
            return unit(projected)
    raise ValueError("Cannot build a frame perpendicular to a zero tangent")


def rotation_minimizing_frames(
    points: Sequence[AtomicPoint],
    tangents: Sequence[AtomicVector],
    first_axis: AtomicVector,
) -> list[AtomicPlane]:
    """Frames at the given samples, X carried along by double reflection from ``first_axis``."""
    if len(points) != len(tangents):
        raise ValueError("points and tangents must pair up")
    frames: list[AtomicPlane] = []
    if not points:
        return frames
    axis = unit(_reject(first_axis, unit(tangents[0])))
    for index, (point, tangent) in enumerate(zip(points, tangents)):
        direction = unit(tangent)
        frames.append(AtomicPlane(origin=point, normal=direction, x_axis=axis))
        if index + 1 < len(points):
            axis = _double_reflection(point, direction, axis, points[index + 1], unit(tangents[index + 1]))
    return frames


def _double_reflection(point, tangent, axis, next_point, next_tangent) -> AtomicVector:
    """Carry ``axis`` from (point, tangent) to (next_point, next_tangent) with minimal rotation."""
    chord = sub(next_point, point)
    chord_squared = dot(chord, chord)
    if chord_squared <= _STRAIGHT * _STRAIGHT:
        return unit(_reject(axis, next_tangent))
    reflected_axis = sub(axis, scale(chord, 2.0 * dot(chord, axis) / chord_squared))
    reflected_tangent = sub(tangent, scale(chord, 2.0 * dot(chord, tangent) / chord_squared))
    second = sub(next_tangent, reflected_tangent)
    second_squared = dot(second, second)
    if second_squared <= _STRAIGHT * _STRAIGHT:
        return unit(_reject(reflected_axis, next_tangent))
    carried = sub(reflected_axis, scale(second, 2.0 * dot(second, reflected_axis) / second_squared))
    return unit(_reject(carried, next_tangent))


def _reject(vector: AtomicVector, direction: AtomicVector) -> AtomicVector:
    """Component of ``vector`` perpendicular to the unit ``direction``."""
    return sub(vector, scale(direction, dot(vector, direction)))


def curve_perpendicular_frames(curve, parameters: Sequence[float], align: bool = True, substeps: int = 16) -> list[AtomicPlane]:
    """Perpendicular frames at *parameters* on any curve atom.

    ``align=False`` builds every frame independently (Rhino's default X axis);
    ``align=True`` sweeps a rotation-minimising frame from the curvature
    direction at the first parameter, propagating through ``substeps``
    intermediate samples per interval so the result is the converged
    zero-twist frame Grasshopper reports.
    """
    from pyhopper.Utils.Curves import curve_curvature_vector, curve_point_at, curve_tangent_at

    if not parameters:
        return []
    # Rhino evaluates the tangent at a polyline vertex from the segment that ends there
    if not align:
        return [perpendicular_frame(curve_point_at(curve, t), curve_tangent_at(curve, t, incoming=True)) for t in parameters]
    dense: list[float] = []
    for start, end in zip(parameters, parameters[1:]):
        dense.extend(start + (end - start) * step / substeps for step in range(substeps))
    dense.append(parameters[-1])
    points = [curve_point_at(curve, t) for t in dense]
    tangents = [curve_tangent_at(curve, t, incoming=True) for t in dense]
    first = initial_frame_axis(tangents[0], curve_curvature_vector(curve, parameters[0]))
    frames = rotation_minimizing_frames(points, tangents, first)
    return [frames[index * substeps] for index in range(len(parameters))]
