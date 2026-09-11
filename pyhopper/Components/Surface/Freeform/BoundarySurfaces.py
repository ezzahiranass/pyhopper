"""BoundarySurfaces - Create planar surfaces from boundary curves."""

from pyhopper.Core.Atoms import AtomicLine, AtomicPlane, AtomicPoint, AtomicPolyline, AtomicRectangle, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE, SURFACE
from pyhopper.Utils.Adapters.shapely_regions import region_boundaries_from_boundary_edges
from pyhopper.Utils.Curves import evaluate_nurbs_curve, nurbs_curve_domain
from pyhopper.Utils.Surfaces import surface_from_planar_boundary
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Utils.Vectors import cross, sub


_TOLERANCE = 1e-9


def _sample_points(curve) -> list[AtomicPoint]:
    if isinstance(curve, AtomicLine):
        return [curve.start, curve.end]
    if isinstance(curve, AtomicPolyline):
        return list(curve.points)
    if isinstance(curve, AtomicRectangle):
        half_x = abs(float(curve.x_size)) / 2.0
        half_y = abs(float(curve.y_size)) / 2.0
        y_axis = curve.plane.y_axis
        return [
            AtomicPoint(
                curve.plane.origin.x + x * curve.plane.x_axis.x + y * y_axis.x,
                curve.plane.origin.y + x * curve.plane.x_axis.y + y * y_axis.y,
                curve.plane.origin.z + x * curve.plane.x_axis.z + y * y_axis.z,
            )
            for x, y in (
                (-half_x, -half_y),
                (half_x, -half_y),
                (half_x, half_y),
                (-half_x, half_y),
            )
        ]

    nurbs = as_nurbs_curve(curve)
    start, end = nurbs_curve_domain(nurbs)
    return [
        evaluate_nurbs_curve(nurbs, start + (end - start) * index / 8.0)
        for index in range(9)
    ]


def _infer_plane(edges) -> AtomicPlane:
    points = []
    for edge in edges:
        points.extend(_sample_points(edge))

    if len(points) < 3:
        raise ValueError("BoundarySurfaces requires at least three boundary points")

    origin = points[0]
    for index_a in range(1, len(points) - 1):
        x_axis = sub(points[index_a], origin)
        if x_axis.length <= _TOLERANCE:
            continue
        for index_b in range(index_a + 1, len(points)):
            normal = cross(x_axis, sub(points[index_b], origin))
            if normal.length > _TOLERANCE:
                return AtomicPlane(origin=origin, normal=normal, x_axis=x_axis)

    raise ValueError("BoundarySurfaces requires non-collinear boundary edges")


class BoundarySurfaces(Component):
    """Create planar surfaces from a branch of closed boundary curves.

    Each input branch is treated as one unordered set of boundary curves,
    matching Grasshopper's Boundary Surfaces list behavior. The current
    pyhopper atom model supports untrimmed tensor-product surfaces, so output
    is limited to triangular and quadrilateral planar regions.
    """

    inputs = [InputParam("edges", CURVE, Access.LIST)]
    outputs = [OutputParam("surfaces", SURFACE, access=Access.LIST)]

    def generate(self, edges=None):
        if not edges:
            return []
        plane = _infer_plane(edges)
        boundaries = region_boundaries_from_boundary_edges(edges, plane)
        return [surface_from_planar_boundary(outer, holes, plane) for outer, holes in boundaries]
