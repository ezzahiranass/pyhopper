"""Area and volume mass-property utilities."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import (
    AtomicBrep,
    AtomicBox,
    AtomicCircle,
    AtomicCylinder,
    AtomicEllipse,
    AtomicMesh,
    AtomicPoint,
    AtomicPolyline,
    AtomicRectangle,
    AtomicSurface,
    AtomicVector,
)
from pyhopper.Utils.Curves import evaluate_nurbs_curve, nurbs_curve_domain
from pyhopper.Utils.Surfaces import surface_integration_triangles
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


_TOLERANCE = 1e-10


def _vector(a, b):
    return b[0] - a[0], b[1] - a[1], b[2] - a[2]


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _triangle_area_centroid(a, b, c):
    cross = _cross(_vector(a, b), _vector(a, c))
    area = math.sqrt(_dot(cross, cross)) / 2.0
    return area, (
        (a[0] + b[0] + c[0]) / 3.0,
        (a[1] + b[1] + c[1]) / 3.0,
        (a[2] + b[2] + c[2]) / 3.0,
    )


def _triangles(positions, indices):
    return [
        (positions[indices[index]], positions[indices[index + 1]], positions[indices[index + 2]])
        for index in range(0, len(indices), 3)
    ]


def _surface_triangles(surface: AtomicSurface):
    return surface_integration_triangles(surface)


def _mesh_triangles(mesh: AtomicMesh):
    positions = [(point.x, point.y, point.z) for point in mesh.vertices]
    indices = []
    for face in mesh.faces:
        for index in range(1, len(face) - 1):
            indices.extend((face[0], face[index], face[index + 1]))
    return _triangles(positions, indices)


def _curve_integration_points(geometry) -> tuple[AtomicPoint, ...]:
    curve = as_nurbs_curve(geometry)
    start, end = nurbs_curve_domain(curve)
    sample_count = max(64, len(curve.control_points) * 12)
    return tuple(
        evaluate_nurbs_curve(curve, start + (end - start) * index / sample_count)
        for index in range(sample_count + 1)
    )


def _geometry_triangles(geometry):
    if isinstance(geometry, AtomicBox):
        from pyhopper.Utils.Boxes import box_to_brep

        return _geometry_triangles(box_to_brep(geometry))
    if isinstance(geometry, AtomicSurface):
        return _surface_triangles(geometry)
    if isinstance(geometry, AtomicMesh):
        return _mesh_triangles(geometry)
    if isinstance(geometry, AtomicBrep):
        return [triangle for face in geometry.faces for triangle in _surface_triangles(face)]
    raise TypeError(f"Mass properties do not support {type(geometry).__name__}")


def _weighted_centroid(weighted_centroids, total):
    if total <= _TOLERANCE:
        raise ValueError("Geometry has no measurable area or volume")
    return AtomicPoint(
        sum(weight * centroid[0] for weight, centroid in weighted_centroids) / total,
        sum(weight * centroid[1] for weight, centroid in weighted_centroids) / total,
        sum(weight * centroid[2] for weight, centroid in weighted_centroids) / total,
    )


def _triangle_area_properties(triangles):
    weighted = []
    total = 0.0
    for a, b, c in triangles:
        area, centroid = _triangle_area_centroid(a, b, c)
        if area > _TOLERANCE:
            total += area
            weighted.append((area, centroid))
    return total, _weighted_centroid(weighted, total)


def _closed_polyline_properties(points: tuple[AtomicPoint, ...]):
    if len(points) < 4:
        raise ValueError("Area requires a closed planar curve")
    seam_distance = math.sqrt(
        (points[0].x - points[-1].x) ** 2
        + (points[0].y - points[-1].y) ** 2
        + (points[0].z - points[-1].z) ** 2
    )
    if seam_distance > 1e-8:
        raise ValueError("Area requires a closed planar curve")
    points = points[:-1] + (points[0],)
    coordinates = [(point.x, point.y, point.z) for point in points]
    origin = coordinates[0]
    normal = (0.0, 0.0, 0.0)
    for index in range(1, len(coordinates) - 2):
        candidate = _cross(_vector(origin, coordinates[index]), _vector(origin, coordinates[index + 1]))
        length = math.sqrt(_dot(candidate, candidate))
        if length > _TOLERANCE:
            normal = tuple(value / length for value in candidate)
            break
    if normal == (0.0, 0.0, 0.0):
        raise ValueError("Geometry has no measurable area")
    if any(abs(_dot(_vector(origin, point), normal)) > 1e-8 for point in coordinates[1:]):
        raise ValueError("Area requires a planar closed curve")

    signed_total = 0.0
    weighted = [0.0, 0.0, 0.0]
    for index in range(1, len(coordinates) - 2):
        a, b, c = origin, coordinates[index], coordinates[index + 1]
        signed_area = _dot(_cross(_vector(a, b), _vector(a, c)), normal) / 2.0
        centroid = tuple((a[axis] + b[axis] + c[axis]) / 3.0 for axis in range(3))
        signed_total += signed_area
        for axis in range(3):
            weighted[axis] += signed_area * centroid[axis]
    if abs(signed_total) <= _TOLERANCE:
        raise ValueError("Geometry has no measurable area")
    return abs(signed_total), AtomicPoint(*(value / signed_total for value in weighted))


def area_properties(geometry) -> tuple[float, AtomicPoint]:
    """Return area and area centroid for supported geometry."""
    if isinstance(geometry, AtomicCircle):
        return math.pi * geometry.radius * geometry.radius, geometry.center
    if isinstance(geometry, AtomicEllipse):
        return math.pi * geometry.radius_x * geometry.radius_y, geometry.plane.origin
    if isinstance(geometry, AtomicRectangle):
        return abs(geometry.x_size * geometry.y_size), geometry.plane.origin
    if isinstance(geometry, AtomicBox):
        x, y, z = abs(geometry.x_size), abs(geometry.y_size), abs(geometry.z_size)
        return 2.0 * (x * y + x * z + y * z), geometry.plane.origin
    if isinstance(geometry, AtomicCylinder):
        radius = abs(geometry.radius)
        height = abs(geometry.height)
        centroid = AtomicPoint(
            geometry.plane.origin.x + geometry.plane.normal.x * geometry.height / 2.0,
            geometry.plane.origin.y + geometry.plane.normal.y * geometry.height / 2.0,
            geometry.plane.origin.z + geometry.plane.normal.z * geometry.height / 2.0,
        )
        return 2.0 * math.pi * radius * (radius + height), centroid
    if isinstance(geometry, AtomicPolyline):
        return _closed_polyline_properties(geometry.points)
    if not isinstance(geometry, (AtomicSurface, AtomicMesh, AtomicBrep)):
        return _closed_polyline_properties(_curve_integration_points(geometry))
    return _triangle_area_properties(_geometry_triangles(geometry))


def _point_key(point):
    return tuple(round(value, 8) for value in point)


def _is_closed_triangles(triangles) -> bool:
    edge_counts = {}
    for triangle in triangles:
        area, _ = _triangle_area_centroid(*triangle)
        if area <= _TOLERANCE:
            continue
        keys = [_point_key(point) for point in triangle]
        for start, end in ((keys[0], keys[1]), (keys[1], keys[2]), (keys[2], keys[0])):
            edge = tuple(sorted((start, end)))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    return bool(edge_counts) and all(count == 2 for count in edge_counts.values())


def volume_properties(geometry) -> tuple[float, AtomicPoint]:
    """Return numerical volume and centroid for closed Breps, meshes, and surfaces."""
    if isinstance(geometry, AtomicBox):
        return abs(geometry.x_size * geometry.y_size * geometry.z_size), geometry.plane.origin
    if isinstance(geometry, AtomicCylinder):
        centroid = AtomicPoint(
            geometry.plane.origin.x + geometry.plane.normal.x * geometry.height / 2.0,
            geometry.plane.origin.y + geometry.plane.normal.y * geometry.height / 2.0,
            geometry.plane.origin.z + geometry.plane.normal.z * geometry.height / 2.0,
        )
        return math.pi * geometry.radius * geometry.radius * abs(geometry.height), centroid
    if not isinstance(geometry, (AtomicBrep, AtomicMesh, AtomicSurface)):
        raise TypeError("Volume supports closed AtomicBrep, AtomicMesh, AtomicSurface, or AtomicCylinder geometry")
    triangles = _geometry_triangles(geometry)
    if not isinstance(geometry, AtomicBrep) and not _is_closed_triangles(triangles):
        raise ValueError("Volume requires closed geometry")

    vertices = [point for triangle in triangles for point in triangle]
    reference = tuple(sum(point[index] for point in vertices) / len(vertices) for index in range(3))
    weighted = []
    total = 0.0
    for a, b, c in triangles:
        ar = _vector(reference, a)
        br = _vector(reference, b)
        cr = _vector(reference, c)
        volume = abs(_dot(ar, _cross(br, cr))) / 6.0
        if volume <= _TOLERANCE:
            continue
        centroid = tuple((reference[index] + a[index] + b[index] + c[index]) / 4.0 for index in range(3))
        total += volume
        weighted.append((volume, centroid))
    return total, _weighted_centroid(weighted, total)


# ── second moments (Grasshopper's Area / Volume Moments) ───────────


def _quadratic_triangle_integrals(a, b, c):
    """Area and the integrals of x², y², z², xy, yz, zx over a triangle (edge-midpoint rule, exact for quadratics)."""
    area, _ = _triangle_area_centroid(a, b, c)
    mids = [tuple((p[i] + q[i]) / 2.0 for i in range(3)) for p, q in ((a, b), (b, c), (c, a))]
    second = [sum(m[i] * m[j] for m in mids) * area / 3.0 for i, j in ((0, 0), (1, 1), (2, 2), (0, 1), (1, 2), (2, 0))]
    return area, second


def _moments_from(total, first, second_world):
    """Centroid-referenced moments: (∫y²+z², ∫x²+z², ∫x²+y²), (∫x², ∫y², ∫z²) and radii of gyration."""
    if total <= _TOLERANCE:
        raise ValueError("Geometry has no measurable area or volume")
    centroid = tuple(value / total for value in first)
    xx, yy, zz, xy, yz, zx = second_world
    # parallel axis shift to the centroid
    xx -= total * centroid[0] ** 2
    yy -= total * centroid[1] ** 2
    zz -= total * centroid[2] ** 2
    inertia = AtomicVector(yy + zz, xx + zz, xx + yy)
    secondary = AtomicVector(xx, yy, zz)
    gyration = AtomicVector(*(math.sqrt(max(value, 0.0) / total) for value in (inertia.x, inertia.y, inertia.z)))
    return total, AtomicPoint(*centroid), inertia, secondary, gyration


def _accumulate_triangles(triangles):
    total = 0.0
    first = [0.0, 0.0, 0.0]
    second = [0.0] * 6
    for a, b, c in triangles:
        area, quadratics = _quadratic_triangle_integrals(a, b, c)
        if area <= _TOLERANCE:
            continue
        centroid = tuple((a[i] + b[i] + c[i]) / 3.0 for i in range(3))
        total += area
        for i in range(3):
            first[i] += area * centroid[i]
        for i in range(6):
            second[i] += quadratics[i]
    return total, first, second


def _polygon_fan_triangles(points):
    """Signed fan triangulation of a closed planar polygon (exact for simple polygons)."""
    coords = [(p.x, p.y, p.z) for p in points]
    if len(coords) > 1 and all(abs(coords[0][i] - coords[-1][i]) <= 1e-12 for i in range(3)):
        coords = coords[:-1]
    if len(coords) < 3:
        raise ValueError("Area moments need a closed planar curve")
    normal = (0.0, 0.0, 0.0)
    for i in range(len(coords)):
        p, q = coords[i], coords[(i + 1) % len(coords)]
        normal = (normal[0] + (p[1] - q[1]) * (p[2] + q[2]), normal[1] + (p[2] - q[2]) * (p[0] + q[0]), normal[2] + (p[0] - q[0]) * (p[1] + q[1]))
    length = math.sqrt(sum(v * v for v in normal))
    if length <= _TOLERANCE:
        raise ValueError("Area moments need a curve that encloses an area")
    normal = tuple(v / length for v in normal)
    total = 0.0
    first = [0.0, 0.0, 0.0]
    second = [0.0] * 6
    origin = coords[0]
    for i in range(1, len(coords) - 1):
        a, b, c = origin, coords[i], coords[i + 1]
        cross = _cross(_vector(a, b), _vector(a, c))
        signed_area = _dot(cross, normal) / 2.0
        if abs(signed_area) <= _TOLERANCE:
            continue
        mids = [tuple((p[k] + q[k]) / 2.0 for k in range(3)) for p, q in ((a, b), (b, c), (c, a))]
        centroid = tuple((a[k] + b[k] + c[k]) / 3.0 for k in range(3))
        total += signed_area
        for k in range(3):
            first[k] += signed_area * centroid[k]
        for index, (i_, j_) in enumerate(((0, 0), (1, 1), (2, 2), (0, 1), (1, 2), (2, 0))):
            second[index] += sum(m[i_] * m[j_] for m in mids) * signed_area / 3.0
    if total < 0.0:
        total, first, second = -total, [-v for v in first], [-v for v in second]
    return total, first, second


def area_moments(geometry):
    """Grasshopper's Area Moments: area, centroid and the centroid-referenced moments of inertia
    (∫y²+z², ∫x²+z², ∫x²+y²), second moments (∫x², ∫y², ∫z²) and radii of gyration, for planar closed
    curves (exact for polylines, circles and ellipses; sampled for other curves), surfaces, breps and
    meshes."""
    if isinstance(geometry, (AtomicCircle, AtomicEllipse, AtomicRectangle)):
        if isinstance(geometry, AtomicRectangle):
            hx, hy = abs(geometry.x_size) / 2.0, abs(geometry.y_size) / 2.0
            area = 4.0 * hx * hy
            ixx, iyy = area * hy * hy / 3.0, area * hx * hx / 3.0  # ∫y² and ∫x² in plane coordinates
        else:
            rx = float(geometry.radius) if isinstance(geometry, AtomicCircle) else float(geometry.radius_x)
            ry = rx if isinstance(geometry, AtomicCircle) else float(geometry.radius_y)
            area = math.pi * rx * ry
            ixx, iyy = area * ry * ry / 4.0, area * rx * rx / 4.0
        plane = geometry.plane
        # rotate the in-plane second-moment tensor (diag(iyy, ixx, 0) in plane axes) to world axes
        x_axis, y_axis = plane.x_axis, plane.y_axis
        axes = ((x_axis.x, x_axis.y, x_axis.z), (y_axis.x, y_axis.y, y_axis.z))
        tensor = [[iyy * axes[0][i] * axes[0][j] + ixx * axes[1][i] * axes[1][j] for j in range(3)] for i in range(3)]
        origin = plane.origin
        second = [tensor[0][0] + area * origin.x ** 2, tensor[1][1] + area * origin.y ** 2, tensor[2][2] + area * origin.z ** 2,
                  tensor[0][1] + area * origin.x * origin.y, tensor[1][2] + area * origin.y * origin.z, tensor[2][0] + area * origin.z * origin.x]
        return _moments_from(area, [area * origin.x, area * origin.y, area * origin.z], second)
    if isinstance(geometry, AtomicPolyline):
        return _moments_from(*_polygon_fan_triangles(geometry.points))
    if isinstance(geometry, (AtomicSurface, AtomicBrep)) or hasattr(geometry, "surface"):
        return _moments_from(*_surface_like_moments(geometry))
    if isinstance(geometry, (AtomicMesh, AtomicBox)):
        return _moments_from(*_accumulate_triangles(_geometry_triangles(geometry)))
    return _moments_from(*_polygon_fan_triangles(_curve_integration_points(geometry)))


def volume_moments(geometry):
    """Grasshopper's Volume Moments: volume, centroid and the centroid-referenced moments of inertia,
    second moments and radii of gyration of a closed brep, mesh or box (tetrahedra from the vertex
    average, like :func:`volume_properties`)."""
    if not isinstance(geometry, (AtomicBrep, AtomicMesh, AtomicSurface, AtomicBox)):
        raise TypeError("Volume moments support closed AtomicBrep, AtomicMesh, AtomicSurface or AtomicBox geometry")
    triangles = _geometry_triangles(geometry)
    if not isinstance(geometry, (AtomicBrep, AtomicBox)) and not _is_closed_triangles(triangles):
        raise ValueError("Volume moments require closed geometry")
    vertices = [point for triangle in triangles for point in triangle]
    reference = tuple(sum(point[index] for point in vertices) / len(vertices) for index in range(3))
    total = 0.0
    first = [0.0, 0.0, 0.0]
    second = [0.0] * 6
    for a, b, c in triangles:
        volume = abs(_dot(_vector(reference, a), _cross(_vector(reference, b), _vector(reference, c)))) / 6.0
        if volume <= _TOLERANCE:
            continue
        corners = (reference, a, b, c)
        total += volume
        for k in range(3):
            first[k] += volume * sum(v[k] for v in corners) / 4.0
        for index, (i, j) in enumerate(((0, 0), (1, 1), (2, 2), (0, 1), (1, 2), (2, 0))):
            # ∫ x_i x_j dV over a tetrahedron = V/20 · (Σ_k v_k,i v_k,j + Σ_k v_k,i · Σ_k v_k,j)
            second[index] += volume / 20.0 * (sum(v[i] * v[j] for v in corners) + sum(v[i] for v in corners) * sum(v[j] for v in corners))
    return _moments_from(total, first, second)


# ── Gauss-Legendre surface integration (smooth NURBS faces) ────────

_GAUSS_ORDER = 12


def _gauss_legendre(order: int) -> tuple[list[float], list[float]]:
    """Nodes and weights on [-1, 1] by Newton iteration on the Legendre polynomial."""
    nodes, weights = [], []
    for i in range(1, order + 1):
        x = math.cos(math.pi * (i - 0.25) / (order + 0.5))
        for _ in range(100):
            p0, p1 = 1.0, x
            for k in range(2, order + 1):
                p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
            derivative = order * (x * p1 - p0) / (x * x - 1.0)
            step = p1 / derivative
            x -= step
            if abs(step) < 1e-15:
                break
        p0, p1 = 1.0, x
        for k in range(2, order + 1):
            p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
        derivative = order * (x * p1 - p0) / (x * x - 1.0)
        nodes.append(x)
        weights.append(2.0 / ((1.0 - x * x) * derivative * derivative))
    return nodes, weights


def _unique_knots(knots, mults, degree):
    expanded = []
    for knot, mult in zip(knots, mults):
        expanded.extend([knot] * mult)
    active = expanded[degree: len(expanded) - degree]
    unique = []
    for knot in active:
        if not unique or knot > unique[-1] + 1e-12:
            unique.append(knot)
    return unique


def _surface_gauss_moments(surface: AtomicSurface):
    """Area, first moments and world second moments of a NURBS surface by Gauss-Legendre quadrature
    over every knot span (accurate to round-off for smooth faces)."""
    from pyhopper.Utils.Nurbs import surface_derivatives

    nodes, weights = _gauss_legendre(_GAUSS_ORDER)
    u_spans = _unique_knots(surface.u_knots, surface.u_mults, surface.u_degree)
    v_spans = _unique_knots(surface.v_knots, surface.v_mults, surface.v_degree)
    total = 0.0
    first = [0.0, 0.0, 0.0]
    second = [0.0] * 6
    for u0, u1 in zip(u_spans, u_spans[1:]):
        for v0, v1 in zip(v_spans, v_spans[1:]):
            scale = (u1 - u0) * (v1 - v0) / 4.0
            for xu, wu in zip(nodes, weights):
                u = (u0 + u1) / 2.0 + xu * (u1 - u0) / 2.0
                for xv, wv in zip(nodes, weights):
                    v = (v0 + v1) / 2.0 + xv * (v1 - v0) / 2.0
                    ders = surface_derivatives(surface, u, v, 1)
                    normal = _cross((ders.du.x, ders.du.y, ders.du.z), (ders.dv.x, ders.dv.y, ders.dv.z))
                    element = math.sqrt(_dot(normal, normal)) * wu * wv * scale
                    p = (ders.point.x, ders.point.y, ders.point.z)
                    total += element
                    for k in range(3):
                        first[k] += element * p[k]
                    for index, (i, j) in enumerate(((0, 0), (1, 1), (2, 2), (0, 1), (1, 2), (2, 0))):
                        second[index] += element * p[i] * p[j]
    return total, first, second


def _surface_like_moments(geometry):
    if isinstance(geometry, AtomicSurface):
        return _surface_gauss_moments(geometry)
    if isinstance(geometry, AtomicBrep):
        total, first, second = 0.0, [0.0, 0.0, 0.0], [0.0] * 6
        for face in geometry.faces:
            face_total, face_first, face_second = _surface_like_moments(face)
            total += face_total
            first = [a + b for a, b in zip(first, face_first)]
            second = [a + b for a, b in zip(second, face_second)]
        return total, first, second
    if hasattr(geometry, "surface"):  # trimmed surface: the untrimmed face
        return _surface_gauss_moments(geometry.surface)
    return _accumulate_triangles(_geometry_triangles(geometry))
