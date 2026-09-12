"""Rectangle construction shared by Rectangle and Rectangle 2Pt.

A sharp rectangle is an ``AtomicRectangle`` (centred plane + sizes). A filleted
one is the polycurve Grasshopper builds: straight edges as lines, corners as
quarter arcs, spans accumulating the segment lengths, starting on the bottom
edge just past the bottom-left corner and running counter-clockwise. Edges
shortened to nothing by the fillet are dropped, exactly like Grasshopper.
"""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicArc, AtomicInterval, AtomicLine, AtomicPlane, AtomicPoint, AtomicPolyCurve, AtomicRectangle, AtomicVector
from pyhopper.Utils.Planes import plane_coordinates, point_on_plane

def rectangle_from_corners(plane: AtomicPlane, corner_a: AtomicPoint, corner_b: AtomicPoint) -> tuple[AtomicPlane, float, float]:
    """(centred plane, width, height) of the rectangle spanned by two points projected onto ``plane``."""
    ax, ay, _ = plane_coordinates(plane, corner_a)
    bx, by, _ = plane_coordinates(plane, corner_b)
    centre = point_on_plane(plane, (ax + bx) / 2.0, (ay + by) / 2.0)
    return AtomicPlane(origin=centre, normal=plane.normal, x_axis=plane.x_axis), abs(bx - ax), abs(by - ay)


def clamp_fillet(width: float, height: float, radius: float) -> float:
    return max(0.0, min(float(radius), width / 2.0, height / 2.0))


def rectangle_length(width: float, height: float, fillet: float = 0.0) -> float:
    return 2.0 * (width + height) - 8.0 * fillet + 2.0 * math.pi * fillet


def make_rectangle(plane: AtomicPlane, width: float, height: float, radius: float = 0.0) -> tuple[AtomicRectangle | AtomicPolyCurve, float]:
    """(rectangle or filleted curve, perimeter) centred on ``plane``."""
    width, height = abs(float(width)), abs(float(height))
    fillet = clamp_fillet(width, height, radius)
    if fillet <= 0.0:
        return AtomicRectangle(plane=plane, x_size=width, y_size=height), rectangle_length(width, height)
    return rounded_rectangle(plane, width, height, fillet), rectangle_length(width, height, fillet)


def rounded_rectangle(plane: AtomicPlane, width: float, height: float, fillet: float) -> AtomicPolyCurve:
    """Rectangle with filleted corners as Grasshopper builds it: a polycurve of edge lines and quarter
    arcs (natural spans), counter-clockwise from the bottom edge's first tangent point; edges that the
    fillets consume entirely vanish."""
    half_x, half_y = width / 2.0, height / 2.0
    x0, x1, y0, y1 = -half_x, half_x, -half_y, half_y
    r = fillet
    # (start, end) of each straight edge and (centre, start) of each quarter arc, counter-clockwise from the bottom edge
    edges = [((x0 + r, y0), (x1 - r, y0)), ((x1, y0 + r), (x1, y1 - r)), ((x1 - r, y1), (x0 + r, y1)), ((x0, y1 - r), (x0, y0 + r))]
    corners = [((x1 - r, y0 + r), (x1 - r, y0)), ((x1 - r, y1 - r), (x1, y1 - r)), ((x0 + r, y1 - r), (x0 + r, y1)), ((x0 + r, y0 + r), (x0, y0 + r))]
    segments: list = []
    for (edge_start, edge_end), (centre, arc_start) in zip(edges, corners):
        if math.hypot(edge_end[0] - edge_start[0], edge_end[1] - edge_start[1]) > 1e-12:
            segments.append(AtomicLine(point_on_plane(plane, *edge_start), point_on_plane(plane, *edge_end)))
        origin = point_on_plane(plane, *centre)
        start_point = point_on_plane(plane, *arc_start)
        x_axis = AtomicVector((start_point.x - origin.x) / r, (start_point.y - origin.y) / r, (start_point.z - origin.z) / r)
        segments.append(AtomicArc(AtomicPlane(origin, plane.normal, x_axis), r, AtomicInterval(0.0, math.pi / 2.0)))
    return AtomicPolyCurve(tuple(segments), tuple(rectangle_spans(segments, r)), 0.0)


def rectangle_spans(segments, radius: float) -> list[float]:
    spans = []
    for segment in segments:
        if isinstance(segment, AtomicLine):
            spans.append(math.dist((segment.start.x, segment.start.y, segment.start.z), (segment.end.x, segment.end.y, segment.end.z)))
        else:
            spans.append(math.pi * radius / 2.0)
    return spans
