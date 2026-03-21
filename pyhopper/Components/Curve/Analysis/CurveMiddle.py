"""CurveMiddle - Return the midpoint of a supported curve."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicArc, AtomicCircle, AtomicLine, AtomicPoint, AtomicPolyline
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _distance(a: AtomicPoint, b: AtomicPoint) -> float:
    dx = b.x - a.x
    dy = b.y - a.y
    dz = b.z - a.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _lerp_point(a: AtomicPoint, b: AtomicPoint, t: float) -> AtomicPoint:
    return AtomicPoint(
        a.x + (b.x - a.x) * t,
        a.y + (b.y - a.y) * t,
        a.z + (b.z - a.z) * t,
    )


def _polyline_middle(polyline: AtomicPolyline) -> AtomicPoint:
    if not polyline.points:
        raise ValueError("CurveMiddle cannot evaluate an empty polyline")
    if len(polyline.points) == 1:
        return polyline.points[0]

    segment_lengths = [
        _distance(polyline.points[index], polyline.points[index + 1])
        for index in range(len(polyline.points) - 1)
    ]
    total_length = sum(segment_lengths)
    if total_length == 0.0:
        return polyline.points[0]

    target_length = total_length / 2.0
    traversed = 0.0

    for index, segment_length in enumerate(segment_lengths):
        next_traversed = traversed + segment_length
        if target_length <= next_traversed:
            if segment_length == 0.0:
                return polyline.points[index]
            local_t = (target_length - traversed) / segment_length
            return _lerp_point(polyline.points[index], polyline.points[index + 1], local_t)
        traversed = next_traversed

    return polyline.points[-1]


def _circle_middle(circle: AtomicCircle) -> AtomicPoint:
    plane = circle.plane
    return AtomicPoint(
        plane.origin.x - circle.radius * plane.x_axis.x,
        plane.origin.y - circle.radius * plane.x_axis.y,
        plane.origin.z - circle.radius * plane.x_axis.z,
    )


def _arc_middle(arc: AtomicArc) -> AtomicPoint:
    plane = arc.plane
    angle = arc.angle.mid
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    x_axis = plane.x_axis
    y_axis = plane.y_axis

    return AtomicPoint(
        plane.origin.x + arc.radius * (cos_angle * x_axis.x + sin_angle * y_axis.x),
        plane.origin.y + arc.radius * (cos_angle * x_axis.y + sin_angle * y_axis.y),
        plane.origin.z + arc.radius * (cos_angle * x_axis.z + sin_angle * y_axis.z),
    )


class CurveMiddle(Component):
    """Return the midpoint of a supported curve as an ``AtomicPoint``.

    Accepts ``AtomicLine``, ``AtomicCircle``, ``AtomicArc``, or
    ``AtomicPolyline`` and returns one midpoint per input item while the
    inherited solve pipeline preserves the surrounding ``DataTree`` structure.
    """

    inputs = [InputParam("curve", None, Access.ITEM)]
    outputs = [OutputParam("point", AtomicPoint)]

    def generate(self, curve=None):
        """Return the midpoint of the incoming curve."""
        if isinstance(curve, AtomicLine):
            return curve.midpoint
        if isinstance(curve, AtomicCircle):
            return _circle_middle(curve)
        if isinstance(curve, AtomicArc):
            return _arc_middle(curve)
        if isinstance(curve, AtomicPolyline):
            return _polyline_middle(curve)

        raise TypeError(
            f"CurveMiddle does not support curve type {type(curve).__name__}"
        )
