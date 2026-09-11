"""Vectors - shared vector algebra on ``AtomicPoint`` / ``AtomicVector``.

Every function is pure and duck-typed on ``.x/.y/.z`` so points and vectors
mix freely where that makes geometric sense (``add(point, vector)`` is a
point, ``sub(point, point)`` is a vector). Components and utilities must use
these instead of local ``_dot`` / ``_cross`` copies.
"""

from __future__ import annotations

import math
from typing import Any

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector

ZERO_TOLERANCE = 1e-12


def dot(a: Any, b: Any) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


def cross(a: Any, b: Any) -> AtomicVector:
    return AtomicVector(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    )


def add(a: Any, b: Any) -> Any:
    """Component-wise sum: point + vector → point, vector + vector → vector."""
    result_type = AtomicPoint if isinstance(a, AtomicPoint) or isinstance(b, AtomicPoint) else AtomicVector
    return result_type(a.x + b.x, a.y + b.y, a.z + b.z)


def sub(a: Any, b: Any) -> AtomicVector:
    """Component-wise difference as a vector (``a - b``)."""
    return AtomicVector(a.x - b.x, a.y - b.y, a.z - b.z)


def scale(v: Any, factor: float) -> Any:
    result_type = AtomicPoint if isinstance(v, AtomicPoint) else AtomicVector
    return result_type(v.x * factor, v.y * factor, v.z * factor)


def negate(v: Any) -> AtomicVector:
    return AtomicVector(-v.x, -v.y, -v.z)


def length(v: Any) -> float:
    return math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)


def is_zero(v: Any, tolerance: float = ZERO_TOLERANCE) -> bool:
    return length(v) <= tolerance


def unit(v: Any) -> AtomicVector:
    """Unit vector in the direction of *v*; the zero vector stays zero."""
    magnitude = length(v)
    if magnitude == 0.0:
        return AtomicVector(0.0, 0.0, 0.0)
    return AtomicVector(v.x / magnitude, v.y / magnitude, v.z / magnitude)


def distance(a: Any, b: Any) -> float:
    return math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2 + (b.z - a.z) ** 2)


def lerp(a: Any, b: Any, t: float) -> Any:
    """Linear interpolation ``a + t * (b - a)``; keeps the type of *a*."""
    result_type = AtomicPoint if isinstance(a, AtomicPoint) else AtomicVector
    return result_type(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t)


def midpoint(a: Any, b: Any) -> AtomicPoint:
    return AtomicPoint((a.x + b.x) * 0.5, (a.y + b.y) * 0.5, (a.z + b.z) * 0.5)


def translate(point: Any, vector: Any, factor: float = 1.0) -> AtomicPoint:
    """``point + factor * vector`` as a point."""
    return AtomicPoint(point.x + vector.x * factor, point.y + vector.y * factor, point.z + vector.z * factor)


def vector_between(a: Any, b: Any) -> AtomicVector:
    """Vector from *a* to *b*."""
    return AtomicVector(b.x - a.x, b.y - a.y, b.z - a.z)


def angle(a: Any, b: Any) -> float:
    """Unsigned angle between two vectors in radians (0 for a zero vector)."""
    denominator = length(a) * length(b)
    if denominator <= ZERO_TOLERANCE:
        return 0.0
    cosine = max(-1.0, min(1.0, dot(a, b) / denominator))
    return math.acos(cosine)


def perpendicular(v: Any) -> AtomicVector:
    """A unit vector perpendicular to *v*, chosen like openNURBS ``ON_3dVector::PerpendicularTo``.

    This is the rule Rhino uses to pick a plane's X axis from its normal, so
    frames built from a normal (Plane Normal, Perp Frames, Plane Fit…) match
    Grasshopper axis-for-axis. Returns the zero vector for a zero input.
    """
    x, y, z = float(v.x), float(v.y), float(v.z)
    ax, ay, az = abs(x), abs(y), abs(z)
    if ay > ax:
        if az > ay:
            i, j, k, a, b = 2, 1, 0, z, -y      # |z| > |y| > |x|
        elif az >= ax:
            i, j, k, a, b = 1, 2, 0, y, -z      # |y| >= |z| >= |x|
        else:
            i, j, k, a, b = 1, 0, 2, y, -x      # |y| > |x| > |z|
    elif az > ax:
        i, j, k, a, b = 2, 0, 1, z, -x          # |z| > |x| >= |y|
    elif az > ay:
        i, j, k, a, b = 0, 2, 1, x, -z          # |x| >= |z| > |y|
    else:
        i, j, k, a, b = 0, 1, 2, x, -y          # |x| >= |y| >= |z|
    components = [0.0, 0.0, 0.0]
    components[i] = b
    components[j] = a
    components[k] = 0.0
    return unit(AtomicVector(*components))
