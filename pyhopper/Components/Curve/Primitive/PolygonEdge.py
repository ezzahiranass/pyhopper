"""PolygonEdge - Create a polygon from a single edge (Grasshopper "Polygon Edge")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicPolyline
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Utils.Planes import point_on_plane
from pyhopper.Utils.Vectors import cross, is_zero, length, sub, translate, unit, vector_between
from pyhopper.Core.TypeSystem import CURVE


class PolygonEdge(Component):
    """Create a polygon from a single edge.

    Inputs:
        edge_start: Start point of polygon edge. (Grasshopper Edge Start [item]).
        edge_end: End point of polygon edge. (Grasshopper Edge End [item]).
        plane_point: Point on polygon plane. (Grasshopper Plane Point [item]).
        segments: Number of segments (Grasshopper Segments [item]).

    Outputs:
        polygon: Polygon (Grasshopper Polygon).
        centre: Centre of polygon (Grasshopper Centre).
        corner_radius: Distance from centre to polygon corner. (Grasshopper Corner Radius).
        edge_radius: Distance from centre to edge mid-points. (Grasshopper Edge Radius).

    Notes:
        Grasshopper: Curve > Primitive > Polygon Edge (PolEdge).
        pyhopper decisions: a regular polygon whose first edge runs from E0 to E1 and which lies on the
        side of the plane point (Grasshopper-verified vertex order); outputs the closed polyline, the
        centre, the corner (circum-) radius and the edge (in-) radius. Fewer than three segments or a
        plane point on the edge line raise ``ValueError``.
    """

    display_name = "Polygon Edge"
    nickname = "PolEdge"
    gh_guid = "f4568ce6-aade-4511-8f32-f27d8a6bf9e9"

    inputs = [
        InputParam("edge_start", AtomicPoint, Access.ITEM),
        InputParam("edge_end", AtomicPoint, Access.ITEM),
        InputParam("plane_point", AtomicPoint, Access.ITEM),
        InputParam("segments", int, Access.ITEM, default=6),
    ]
    outputs = [
        OutputParam("polygon", CURVE),
        OutputParam("centre", AtomicPoint),
        OutputParam("corner_radius", float),
        OutputParam("edge_radius", float),
    ]

    def generate(self, edge_start=None, edge_end=None, plane_point=None, segments=6):
        count = int(segments)
        if count < 3:
            raise ValueError("PolygonEdge needs at least three segments")
        edge = vector_between(edge_start, edge_end)
        normal = cross(edge, sub(plane_point, edge_start))
        if is_zero(normal):
            raise ValueError("PolygonEdge needs a plane point off the edge")
        side = length(edge)
        inward = unit(cross(normal, edge))  # points towards the plane point
        edge_radius = side / (2.0 * math.tan(math.pi / count))
        corner_radius = side / (2.0 * math.sin(math.pi / count))
        centre = translate(translate(edge_start, edge, 0.5), inward, edge_radius)
        plane = AtomicPlane(centre, normal, sub(edge_start, centre))
        step = 2.0 * math.pi / count
        corners = [point_on_plane(plane, corner_radius * math.cos(k * step), corner_radius * math.sin(k * step)) for k in range(count)]
        return AtomicPolyline(tuple(corners + [corners[0]])), centre, corner_radius, edge_radius
