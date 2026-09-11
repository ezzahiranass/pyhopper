"""Surface evaluation and numerical integration utilities."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicPolyline, AtomicSurface, AtomicTrimmedSurface


_SUBDIVISIONS_PER_SPAN = {1: 1, 2: 16, 3: 12}
_POINT_TOLERANCE = 1e-7


def _point_distance(a: AtomicPoint, b: AtomicPoint) -> float:
    return ((b.x - a.x) ** 2 + (b.y - a.y) ** 2 + (b.z - a.z) ** 2) ** 0.5


def _point_on_plane(plane: AtomicPlane, x: float, y: float) -> AtomicPoint:
    y_axis = plane.y_axis
    return AtomicPoint(
        plane.origin.x + x * plane.x_axis.x + y * y_axis.x,
        plane.origin.y + x * plane.x_axis.y + y * y_axis.y,
        plane.origin.z + x * plane.x_axis.z + y * y_axis.z,
    )


def _point_to_plane_xy(point: AtomicPoint, plane: AtomicPlane) -> tuple[float, float]:
    y_axis = plane.y_axis
    return (
        (point.x - plane.origin.x) * plane.x_axis.x
        + (point.y - plane.origin.y) * plane.x_axis.y
        + (point.z - plane.origin.z) * plane.x_axis.z,
        (point.x - plane.origin.x) * y_axis.x
        + (point.y - plane.origin.y) * y_axis.y
        + (point.z - plane.origin.z) * y_axis.z,
    )


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

    projected = [_point_to_plane_xy(point, plane) for point in all_points]
    min_x = min(x for x, _ in projected)
    max_x = max(x for x, _ in projected)
    min_y = min(y for _, y in projected)
    max_y = max(y for _, y in projected)
    width = max_x - min_x
    height = max_y - min_y
    if width <= _POINT_TOLERANCE or height <= _POINT_TOLERANCE:
        raise ValueError("Trimmed surface boundary must span a non-zero planar area")

    base = surface_from_corners(
        _point_on_plane(plane, min_x, min_y),
        _point_on_plane(plane, max_x, min_y),
        _point_on_plane(plane, max_x, max_y),
        _point_on_plane(plane, min_x, max_y),
    )

    def to_uv_loop(loop: AtomicPolyline) -> AtomicPolyline:
        points = []
        for point in loop.points:
            x, y = _point_to_plane_xy(point, plane)
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


def _expand_knots(knots: tuple[float, ...], mults: tuple[int, ...]) -> tuple[float, ...]:
    return tuple(knot for knot, mult in zip(knots, mults) for _ in range(mult))


def _find_span(degree: int, knots: tuple[float, ...], point_count: int, parameter: float) -> int:
    if parameter >= knots[point_count]:
        return point_count - 1
    low = degree
    high = point_count
    span = (low + high) // 2
    while parameter < knots[span] or parameter >= knots[span + 1]:
        if parameter < knots[span]:
            high = span
        else:
            low = span
        span = (low + high) // 2
    return span


def _basis_functions(span: int, parameter: float, degree: int, knots: tuple[float, ...]) -> list[float]:
    basis = [0.0] * (degree + 1)
    basis[0] = 1.0
    left = [0.0] * (degree + 1)
    right = [0.0] * (degree + 1)
    for order in range(1, degree + 1):
        left[order] = parameter - knots[span + 1 - order]
        right[order] = knots[span + order] - parameter
        saved = 0.0
        for index in range(order):
            denominator = right[index + 1] + left[order - index]
            term = 0.0 if abs(denominator) < 1e-12 else basis[index] / denominator
            basis[index] = saved + right[index + 1] * term
            saved = left[order - index] * term
        basis[order] = saved
    return basis


def evaluate_surface(surface: AtomicSurface, u: float, v: float) -> tuple[float, float, float]:
    """Evaluate an ``AtomicSurface`` at one parameter pair."""
    v_count = len(surface.poles)
    u_count = len(surface.poles[0])
    u_knots = _expand_knots(surface.u_knots, surface.u_mults)
    v_knots = _expand_knots(surface.v_knots, surface.v_mults)
    u_degree = max(1, min(int(surface.u_degree), u_count - 1))
    v_degree = max(1, min(int(surface.v_degree), v_count - 1))
    uu = max(u_knots[u_degree], min(u_knots[u_count], float(u)))
    vv = max(v_knots[v_degree], min(v_knots[v_count], float(v)))
    u_span = _find_span(u_degree, u_knots, u_count, uu)
    v_span = _find_span(v_degree, v_knots, v_count, vv)
    u_basis = _basis_functions(u_span, uu, u_degree, u_knots)
    v_basis = _basis_functions(v_span, vv, v_degree, v_knots)

    x = y = z = total_weight = 0.0
    for v_index, v_value in enumerate(v_basis):
        row = v_span - v_degree + v_index
        for u_index, u_value in enumerate(u_basis):
            column = u_span - u_degree + u_index
            point = surface.poles[row][column]
            coefficient = u_value * v_value * surface.weights[row][column]
            x += coefficient * point.x
            y += coefficient * point.y
            z += coefficient * point.z
            total_weight += coefficient
    if abs(total_weight) < 1e-12:
        raise ValueError("Surface evaluation produced a zero rational weight")
    return x / total_weight, y / total_weight, z / total_weight


def _parameter_samples(knots: tuple[float, ...], mults: tuple[int, ...], degree: int) -> list[float]:
    full_knots = _expand_knots(knots, mults)
    point_count = len(full_knots) - degree - 1
    start = full_knots[degree]
    end = full_knots[point_count]
    boundaries = [start]
    for knot in full_knots[degree + 1:point_count + 1]:
        if knot > boundaries[-1]:
            boundaries.append(knot)
    if boundaries[-1] < end:
        boundaries.append(end)
    subdivisions = _SUBDIVISIONS_PER_SPAN.get(degree, max(6, degree * 2))
    samples = []
    for span_start, span_end in zip(boundaries, boundaries[1:]):
        samples.extend(
            span_start + (span_end - span_start) * index / subdivisions
            for index in range(subdivisions)
        )
    samples.append(boundaries[-1])
    return samples


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
