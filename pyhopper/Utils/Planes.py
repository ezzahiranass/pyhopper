"""Plane coercion helpers for geometry components."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector


def _dot(a: AtomicVector, b: AtomicVector) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


def coerce_base_plane(base, input_name: str = "base") -> AtomicPlane:
    """Coerce a point or plane into a normalized Rhino-style base plane."""
    if isinstance(base, AtomicPoint):
        return AtomicPlane.world_xy(base)
    if not isinstance(base, AtomicPlane):
        raise TypeError(f"{input_name} must be an AtomicPoint or AtomicPlane")

    normal = base.normal.unitize()
    x_axis = base.x_axis.unitize()
    if normal.length == 0.0 or x_axis.length == 0.0:
        raise ValueError(f"{input_name} plane axes must be non-zero")
    if abs(_dot(normal, x_axis)) > 1e-9:
        raise ValueError(f"{input_name} plane normal and x axis must be perpendicular")
    return AtomicPlane(origin=base.origin, normal=normal, x_axis=x_axis)
