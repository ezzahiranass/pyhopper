"""Shared helpers for array transform components."""

from __future__ import annotations

import bisect
import math

from pyhopper.Core.Atoms import (
    AtomicPlane,
    AtomicPoint,
    AtomicTransform,
    AtomicVector,
)
from pyhopper.Utils.Curves import evaluate_nurbs_curve, nurbs_curve_domain
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Utils.Vectors import distance, dot, sub


def checked_count(count: int) -> int:
    value = int(count)
    if value < 1:
        raise ValueError("Array count must be at least one")
    return value


def array_result(geometry, transforms: list[AtomicTransform]):
    return [apply_transform(transform, geometry) for transform in transforms], transforms


def scaled_vector(vector: AtomicVector, factor: float) -> AtomicVector:
    return AtomicVector(vector.x * factor, vector.y * factor, vector.z * factor)


def combined_vector(*vectors: AtomicVector) -> AtomicVector:
    return AtomicVector(
        sum(vector.x for vector in vectors),
        sum(vector.y for vector in vectors),
        sum(vector.z for vector in vectors),
    )


def _project_to_plane(vector: AtomicVector, normal: AtomicVector) -> AtomicVector:
    amount = dot(vector, normal)
    return AtomicVector(
        vector.x - amount * normal.x,
        vector.y - amount * normal.y,
        vector.z - amount * normal.z,
    )


def _initial_frame_axis(tangent: AtomicVector) -> AtomicVector:
    for candidate in (AtomicVector.unit_z(), AtomicVector.unit_x(), AtomicVector.unit_y()):
        projected = _project_to_plane(candidate, tangent)
        if projected.length > 1e-9:
            return projected.unitize()
    raise ValueError("Could not construct a perpendicular curve frame")


def _curve_array_parameters(rail, item_count: int) -> list[float]:
    start, end = nurbs_curve_domain(rail)
    sample_count = max(256, len(rail.control_points) * 32)
    sample_parameters = [
        start + (end - start) * index / sample_count
        for index in range(sample_count + 1)
    ]
    sample_points = [evaluate_nurbs_curve(rail, parameter) for parameter in sample_parameters]
    cumulative = [0.0]
    for left, right in zip(sample_points, sample_points[1:]):
        cumulative.append(cumulative[-1] + distance(left, right))
    total = cumulative[-1]
    if total <= 1e-12:
        raise ValueError("Curve Array requires a non-zero-length rail")

    closed = distance(sample_points[0], sample_points[-1]) <= 1e-8 * max(1.0, total)
    divisor = item_count if closed else max(1, item_count - 1)
    parameters = []
    for index in range(item_count):
        target = total * index / divisor
        upper = min(bisect.bisect_left(cumulative, target), sample_count)
        if upper == 0:
            parameters.append(start)
            continue
        lower = upper - 1
        span_length = cumulative[upper] - cumulative[lower]
        local = 0.0 if span_length <= 1e-12 else (target - cumulative[lower]) / span_length
        parameters.append(sample_parameters[lower] + (sample_parameters[upper] - sample_parameters[lower]) * local)
    return parameters


def curve_array_transforms(curve, count: int) -> list[AtomicTransform]:
    """Create stable plane-to-plane transforms at equal rail-length intervals."""
    item_count = checked_count(count)
    rail = as_nurbs_curve(curve)
    start, end = nurbs_curve_domain(rail)
    parameters = _curve_array_parameters(rail, item_count)
    epsilon = max(abs(end - start) * 1e-6, 1e-9)
    frames = []
    previous_x = None

    for parameter in parameters:
        before = max(start, parameter - epsilon)
        after = min(end, parameter + epsilon)
        tangent = sub(
            evaluate_nurbs_curve(rail, after),
            evaluate_nurbs_curve(rail, before),
        ).unitize()
        if tangent.length == 0.0:
            raise ValueError("Curve Array cannot construct a frame at a stationary rail point")

        x_axis = _initial_frame_axis(tangent) if previous_x is None else _project_to_plane(previous_x, tangent)
        if x_axis.length <= 1e-9:
            x_axis = _initial_frame_axis(tangent)
        x_axis = x_axis.unitize()
        frames.append(AtomicPlane(evaluate_nurbs_curve(rail, parameter), tangent, x_axis))
        previous_x = x_axis

    source = frames[0]
    return [AtomicTransform.orient(source, frame) for frame in frames]
