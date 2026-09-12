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
    # Rhino's face order for a box brep: bottom, then the sides -y, +x, +y, -x, then the top
    return AtomicBrep(faces=(
        _quad_surface(corners[(-1, -1, -1)], corners[(1, -1, -1)], corners[(-1, 1, -1)], corners[(1, 1, -1)]),
        _quad_surface(corners[(-1, -1, -1)], corners[(1, -1, -1)], corners[(-1, -1, 1)], corners[(1, -1, 1)]),
        _quad_surface(corners[(1, -1, -1)], corners[(1, 1, -1)], corners[(1, -1, 1)], corners[(1, 1, 1)]),
        _quad_surface(corners[(-1, 1, -1)], corners[(1, 1, -1)], corners[(-1, 1, 1)], corners[(1, 1, 1)]),
        _quad_surface(corners[(-1, -1, -1)], corners[(-1, 1, -1)], corners[(-1, -1, 1)], corners[(-1, 1, 1)]),
        _quad_surface(corners[(-1, -1, 1)], corners[(1, -1, 1)], corners[(-1, 1, 1)], corners[(1, 1, 1)]),
    ))


def box_corners(box: AtomicBox) -> list[AtomicPoint]:
    """The eight corners in Grasshopper's order: bottom face A-B-C-D counter-clockwise, then the top face E-F-G-H."""
    half_x = float(box.x_size) / 2.0
    half_y = float(box.y_size) / 2.0
    half_z = float(box.z_size) / 2.0
    corners = []
    for z in (-half_z, half_z):
        for x, y in ((-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y)):
            corners.append(_point_on_box(box, x, y, z))
    return corners


def box_from_corners(plane, corner_a: AtomicPoint, corner_b: AtomicPoint) -> AtomicBox:
    """Box aligned to ``plane`` spanned by two corners (their plane coordinates), centred like every pyhopper box."""
    from pyhopper.Utils.Planes import plane_coordinates, point_on_plane

    ax, ay, az = plane_coordinates(plane, corner_a)
    bx, by, bz = plane_coordinates(plane, corner_b)
    centre = point_on_plane(plane, (ax + bx) / 2.0, (ay + by) / 2.0, (az + bz) / 2.0)
    return AtomicBox(type(plane)(origin=centre, normal=plane.normal, x_axis=plane.x_axis), abs(bx - ax), abs(by - ay), abs(bz - az))


def box_intervals(box: AtomicBox):
    """Grasshopper Deconstruct Box domains: the box is centred on its plane, so each is +/- half a size."""
    from pyhopper.Core.Atoms import AtomicInterval

    return tuple(AtomicInterval(-float(size) / 2.0, float(size) / 2.0) for size in (box.x_size, box.y_size, box.z_size))


def _boundary_rows(face) -> list[tuple]:
    """The four pole-grid boundaries of a face, each as a tuple of rounded coordinates."""
    poles = face.surface.poles if hasattr(face, "surface") else face.poles
    rows = [poles[0], poles[-1], tuple(row[0] for row in poles), tuple(row[-1] for row in poles)]
    return [tuple((round(p.x, 9), round(p.y, 9), round(p.z, 9)) for p in row) for row in rows]


def shell_is_closed(brep) -> bool:
    """True when every face boundary matches another face's boundary (either direction)."""
    boundaries = [_boundary_rows(face) for face in brep.faces]
    for index, rows in enumerate(boundaries):
        for row in rows:
            reversed_row = tuple(reversed(row))
            if not any(row in other or reversed_row in other for other_index, other in enumerate(boundaries) if other_index != index):
                return False
    return True
