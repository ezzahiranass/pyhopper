"""Exact conversion utilities for named box atoms."""

from pyhopper.Core.Atoms import AtomicBox, AtomicBrep, AtomicPoint, AtomicSurface


def _point_on_box(box: AtomicBox, x: float, y: float, z: float) -> AtomicPoint:
    plane = box.plane
    y_axis = plane.y_axis
    return AtomicPoint(
        plane.origin.x + plane.x_axis.x * x + y_axis.x * y + plane.normal.x * z,
        plane.origin.y + plane.x_axis.y * x + y_axis.y * y + plane.normal.y * z,
        plane.origin.z + plane.x_axis.z * x + y_axis.z * y + plane.normal.z * z,
    )


def _quad_surface(
    point_00: AtomicPoint,
    point_10: AtomicPoint,
    point_01: AtomicPoint,
    point_11: AtomicPoint,
) -> AtomicSurface:
    return AtomicSurface(
        poles=((point_00, point_10), (point_01, point_11)),
        weights=((1.0, 1.0), (1.0, 1.0)),
        u_knots=(0.0, 1.0),
        v_knots=(0.0, 1.0),
        u_mults=(2, 2),
        v_mults=(2, 2),
        u_degree=1,
        v_degree=1,
    )


def box_to_brep(box: AtomicBox) -> AtomicBrep:
    """Convert a named box into its exact six-face Brep representation."""
    half_x = abs(float(box.x_size)) / 2.0
    half_y = abs(float(box.y_size)) / 2.0
    half_z = abs(float(box.z_size)) / 2.0
    if min(half_x, half_y, half_z) <= 0.0:
        raise ValueError("Box dimensions must be greater than zero")

    corners = {
        (x, y, z): _point_on_box(box, x * half_x, y * half_y, z * half_z)
        for x in (-1, 1)
        for y in (-1, 1)
        for z in (-1, 1)
    }
    return AtomicBrep(faces=(
        _quad_surface(corners[(-1, -1, -1)], corners[(1, -1, -1)], corners[(-1, 1, -1)], corners[(1, 1, -1)]),
        _quad_surface(corners[(-1, -1, 1)], corners[(1, -1, 1)], corners[(-1, 1, 1)], corners[(1, 1, 1)]),
        _quad_surface(corners[(-1, -1, -1)], corners[(1, -1, -1)], corners[(-1, -1, 1)], corners[(1, -1, 1)]),
        _quad_surface(corners[(-1, 1, -1)], corners[(1, 1, -1)], corners[(-1, 1, 1)], corners[(1, 1, 1)]),
        _quad_surface(corners[(-1, -1, -1)], corners[(-1, 1, -1)], corners[(-1, -1, 1)], corners[(-1, 1, 1)]),
        _quad_surface(corners[(1, -1, -1)], corners[(1, 1, -1)], corners[(1, -1, 1)], corners[(1, 1, 1)]),
    ))
