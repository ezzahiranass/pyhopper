"""Plane helpers: coercion, local coordinates and construction from a normal."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Utils.Vectors import dot, perpendicular, unit


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
    if abs(dot(normal, x_axis)) > 1e-9:
        raise ValueError(f"{input_name} plane normal and x axis must be perpendicular")
    return AtomicPlane(origin=base.origin, normal=normal, x_axis=x_axis)


def point_on_plane(plane: AtomicPlane, x: float, y: float, z: float = 0.0) -> AtomicPoint:
    """World point at plane coordinates ``(x, y, z)`` (z along the normal)."""
    y_axis = plane.y_axis
    if z == 0.0:
        return AtomicPoint(
            plane.origin.x + x * plane.x_axis.x + y * y_axis.x,
            plane.origin.y + x * plane.x_axis.y + y * y_axis.y,
            plane.origin.z + x * plane.x_axis.z + y * y_axis.z,
        )
    normal = plane.normal
    return AtomicPoint(
        plane.origin.x + x * plane.x_axis.x + y * y_axis.x + z * normal.x,
        plane.origin.y + x * plane.x_axis.y + y * y_axis.y + z * normal.y,
        plane.origin.z + x * plane.x_axis.z + y * y_axis.z + z * normal.z,
    )


def plane_coordinates(plane: AtomicPlane, point: AtomicPoint) -> tuple[float, float, float]:
    """Plane-local ``(x, y, z)`` coordinates of a world point."""
    dx = point.x - plane.origin.x
    dy = point.y - plane.origin.y
    dz = point.z - plane.origin.z
    y_axis = plane.y_axis
    return (
        dx * plane.x_axis.x + dy * plane.x_axis.y + dz * plane.x_axis.z,
        dx * y_axis.x + dy * y_axis.y + dz * y_axis.z,
        dx * plane.normal.x + dy * plane.normal.y + dz * plane.normal.z,
    )


def plane_xy(plane: AtomicPlane, point: AtomicPoint) -> tuple[float, float]:
    """Plane-local ``(x, y)`` of a world point (orthogonal projection)."""
    x, y, _ = plane_coordinates(plane, point)
    return x, y


def signed_distance(plane: AtomicPlane, point: AtomicPoint) -> float:
    """Distance from the plane along its normal (positive on the normal side)."""
    return plane_coordinates(plane, point)[2]


def project_point(plane: AtomicPlane, point: AtomicPoint) -> AtomicPoint:
    """Closest point on the plane."""
    x, y, _ = plane_coordinates(plane, point)
    return point_on_plane(plane, x, y)


def plane_from_normal(origin: AtomicPoint, normal: AtomicVector) -> AtomicPlane:
    """Plane through *origin* with the given normal; X axis chosen like Rhino."""
    z_axis = unit(normal)
    if z_axis.length == 0.0:
        raise ValueError("plane_from_normal requires a non-zero normal")
    return AtomicPlane(origin=origin, normal=z_axis, x_axis=perpendicular(z_axis))
