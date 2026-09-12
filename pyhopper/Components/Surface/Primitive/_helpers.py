"""Shared helpers for exact surface primitives."""

from pyhopper.Core.Atoms import (
    AtomicBox,
    AtomicCircle,
    AtomicPlane,
    AtomicPoint,
    AtomicSurface,
    _collapse_repeated_knots,
)
from pyhopper.Utils.Planes import coerce_base_plane
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


def point_on_plane(plane: AtomicPlane, x: float, y: float, z: float) -> AtomicPoint:
    y_axis = plane.y_axis
    return AtomicPoint(
        plane.origin.x + plane.x_axis.x * x + y_axis.x * y + plane.normal.x * z,
        plane.origin.y + plane.x_axis.y * x + y_axis.y * y + plane.normal.y * z,
        plane.origin.z + plane.x_axis.z * x + y_axis.z * y + plane.normal.z * z,
    )


def centered_box(base, x_size: float, y_size: float, z_size: float) -> AtomicBox:
    plane = coerce_base_plane(base)
    dimensions = tuple(abs(float(value)) for value in (x_size, y_size, z_size))
    if min(dimensions) <= 0.0:
        raise ValueError("CenterBox dimensions must be greater than zero")
    return AtomicBox(plane=plane, x_size=dimensions[0], y_size=dimensions[1], z_size=dimensions[2])


def circular_surface(base, radius: float, length: float, cone: bool = False) -> tuple[AtomicSurface, AtomicPoint]:
    plane = coerce_base_plane(base)
    surface_radius = abs(float(radius))
    surface_length = float(length)
    if surface_radius <= 0.0:
        raise ValueError("Radius must be greater than zero")
    if surface_length == 0.0:
        raise ValueError("Length must be non-zero")

    circle = as_nurbs_curve(AtomicCircle(plane=plane, radius=surface_radius))
    tip = point_on_plane(plane, 0.0, 0.0, surface_length)
    top_row = tuple(tip for _ in circle.control_points)
    if not cone:
        top_row = tuple(
            AtomicPoint(
                point.x + plane.normal.x * surface_length,
                point.y + plane.normal.y * surface_length,
                point.z + plane.normal.z * surface_length,
            )
            for point in circle.control_points
        )

    u_knots, u_mults = _collapse_repeated_knots(circle.knots)
    return AtomicSurface(
        poles=(circle.control_points, top_row),
        weights=(circle.weights, circle.weights),
        u_knots=u_knots,
        v_knots=(0.0, 1.0),
        u_mults=u_mults,
        v_mults=(2, 2),
        u_degree=circle.degree,
        v_degree=1,
    ), tip
