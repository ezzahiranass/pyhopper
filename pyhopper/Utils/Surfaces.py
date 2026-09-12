"""Surface evaluation and numerical integration utilities."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicPolyline, AtomicSurface, AtomicTrimmedSurface
from pyhopper.Utils.Nurbs import SUBDIVISIONS_PER_SPAN as _SUBDIVISIONS_PER_SPAN
from pyhopper.Utils.Nurbs import span_parameter_samples, surface_point_xyz
from pyhopper.Utils.Planes import plane_xy, point_on_plane
from pyhopper.Utils.Vectors import distance as _point_distance


_POINT_TOLERANCE = 1e-7


def surface_from_corners(
    corner_a: AtomicPoint,
    corner_b: AtomicPoint,
    corner_c: AtomicPoint,
    corner_d: AtomicPoint | None = None,
) -> AtomicSurface:
    """Create a bilinear surface from three or four corner points.

    Three-corner input creates a degenerate bilinear patch whose fourth corner
    is duplicated from ``corner_c``. Four-corner input uses the same corner
    order as Grasshopper's 4Point Surface component: A, B, C, D around the
    boundary.
    """
    if corner_d is None:
        corner_d = corner_c

    return AtomicSurface(
        poles=((corner_a, corner_b), (corner_d, corner_c)),
        weights=((1.0, 1.0), (1.0, 1.0)),
        u_knots=(0.0, 1.0),
        v_knots=(0.0, 1.0),
        u_mults=(2, 2),
        v_mults=(2, 2),
        u_degree=1,
        v_degree=1,
    )


def surface_from_closed_polyline(polyline) -> AtomicSurface:
    """Create a bilinear surface from a closed triangular or quad polyline."""
    points = list(polyline.points)
    if len(points) > 1 and _point_distance(points[0], points[-1]) <= _POINT_TOLERANCE:
        points = points[:-1]

    unique: list[AtomicPoint] = []
    for point in points:
        if not unique or _point_distance(unique[-1], point) > _POINT_TOLERANCE:
            unique.append(point)

    if len(unique) == 3:
        return surface_from_corners(unique[0], unique[1], unique[2])
    if len(unique) == 4:
        return surface_from_corners(unique[0], unique[1], unique[2], unique[3])

    raise ValueError(
        "BoundarySurfaces can currently create AtomicSurface output only from "
        "triangular or quadrilateral planar boundary regions."
    )


def trimmed_surface_from_planar_loops(
    outer: AtomicPolyline,
    holes: tuple[AtomicPolyline, ...],
    plane: AtomicPlane,
) -> AtomicTrimmedSurface:
    """Create a planar trimmed surface from 3-D boundary loops."""
    all_points = [*outer.points]
    for hole in holes:
        all_points.extend(hole.points)
    if len(all_points) < 3:
        raise ValueError("Trimmed surface requires at least three boundary points")

    projected = [plane_xy(plane, point) for point in all_points]
    min_x = min(x for x, _ in projected)
    max_x = max(x for x, _ in projected)
    min_y = min(y for _, y in projected)
    max_y = max(y for _, y in projected)
    width = max_x - min_x
    height = max_y - min_y
    if width <= _POINT_TOLERANCE or height <= _POINT_TOLERANCE:
        raise ValueError("Trimmed surface boundary must span a non-zero planar area")

    base = surface_from_corners(
        point_on_plane(plane, min_x, min_y),
        point_on_plane(plane, max_x, min_y),
        point_on_plane(plane, max_x, max_y),
        point_on_plane(plane, min_x, max_y),
    )

    def to_uv_loop(loop: AtomicPolyline) -> AtomicPolyline:
        points = []
        for point in loop.points:
            x, y = plane_xy(plane, point)
            points.append(AtomicPoint((x - min_x) / width, (y - min_y) / height, 0.0))
        return AtomicPolyline(points=tuple(points))

    return AtomicTrimmedSurface(
        surface=base,
        outer=to_uv_loop(outer),
        holes=tuple(to_uv_loop(hole) for hole in holes),
    )


def surface_from_planar_boundary(
    outer: AtomicPolyline,
    holes: tuple[AtomicPolyline, ...],
    plane: AtomicPlane,
) -> AtomicSurface | AtomicTrimmedSurface:
    """Create a plain or trimmed planar surface from one boundary region."""
    if not holes:
        try:
            return surface_from_closed_polyline(outer)
        except ValueError:
            pass
    return trimmed_surface_from_planar_loops(outer, holes, plane)


def evaluate_surface(surface: AtomicSurface, u: float, v: float) -> tuple[float, float, float]:
    """Evaluate an ``AtomicSurface`` at one parameter pair."""
    return surface_point_xyz(surface, u, v)


def _parameter_samples(knots: tuple[float, ...], mults: tuple[int, ...], degree: int) -> list[float]:
    return span_parameter_samples(knots, mults, degree, _SUBDIVISIONS_PER_SPAN)


def surface_integration_triangles(surface: AtomicSurface):
    """Return knot-aware surface panels for numerical integration."""
    u_samples = _parameter_samples(surface.u_knots, surface.u_mults, surface.u_degree)
    v_samples = _parameter_samples(surface.v_knots, surface.v_mults, surface.v_degree)
    points = [[evaluate_surface(surface, u, v) for u in u_samples] for v in v_samples]
    triangles = []
    for row in range(len(v_samples) - 1):
        for column in range(len(u_samples) - 1):
            a = points[row][column]
            b = points[row][column + 1]
            c = points[row + 1][column]
            d = points[row + 1][column + 1]
            triangles.extend(((a, b, d), (a, d, c)))
    return triangles
