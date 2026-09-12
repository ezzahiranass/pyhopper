"""Rectangle construction shared by Rectangle and Rectangle 2Pt.

A sharp rectangle is an ``AtomicRectangle`` (centred plane + sizes). A filleted
one is the exact rational degree-2 NURBS Grasshopper builds: straight edges as
3-point spans, corners as quarter-circle spans (middle weight sqrt(2)/2), knots
accumulating the segment lengths, starting on the bottom edge just past the
bottom-left corner and running counter-clockwise. Edges shortened to nothing by
the fillet are dropped, exactly like Grasshopper.
"""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicNurbsCurve, AtomicPlane, AtomicPoint, AtomicRectangle
from pyhopper.Utils.Planes import plane_coordinates, point_on_plane

_CORNER_WEIGHT = math.sqrt(0.5)


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


def make_rectangle(plane: AtomicPlane, width: float, height: float, radius: float = 0.0) -> tuple[AtomicRectangle | AtomicNurbsCurve, float]:
    """(rectangle or filleted curve, perimeter) centred on ``plane``."""
    width, height = abs(float(width)), abs(float(height))
    fillet = clamp_fillet(width, height, radius)
    if fillet <= 0.0:
        return AtomicRectangle(plane=plane, x_size=width, y_size=height), rectangle_length(width, height)
    return rounded_rectangle(plane, width, height, fillet), rectangle_length(width, height, fillet)


def rounded_rectangle(plane: AtomicPlane, width: float, height: float, fillet: float) -> AtomicNurbsCurve:
    """Exact NURBS of a rectangle with filleted corners (Grasshopper's construction)."""
    half_x, half_y = width / 2.0, height / 2.0
    x0, x1, y0, y1 = -half_x, half_x, -half_y, half_y
    r = fillet
    # (start, end) of each straight edge and (corner, end) of each quarter arc, counter-clockwise from the bottom edge
    edges = [((x0 + r, y0), (x1 - r, y0)), ((x1, y0 + r), (x1, y1 - r)), ((x1 - r, y1), (x0 + r, y1)), ((x0, y1 - r), (x0, y0 + r))]
    corners = [((x1, y0), (x1, y0 + r)), ((x1, y1), (x1 - r, y1)), ((x0, y1), (x0, y1 - r)), ((x0, y0), (x0 + r, y0))]

    local: list[tuple[float, float]] = [edges[0][0]]
    weights = [1.0]
    spans: list[float] = []
    for (edge_start, edge_end), (corner, corner_end) in zip(edges, corners):
        edge_length = math.hypot(edge_end[0] - edge_start[0], edge_end[1] - edge_start[1])
        if edge_length > 1e-12:
            local.append(((edge_start[0] + edge_end[0]) / 2.0, (edge_start[1] + edge_end[1]) / 2.0))
            local.append(edge_end)
            weights.extend([1.0, 1.0])
            spans.append(edge_length)
        local.append(corner)
        local.append(corner_end)
        weights.extend([_CORNER_WEIGHT, 1.0])
        spans.append(math.pi * r / 2.0)

    knots = [0.0, 0.0, 0.0]
    total = 0.0
    for span in spans[:-1]:
        total += span
        knots.extend([total, total])
    total += spans[-1]
    knots.extend([total, total, total])
    points = tuple(point_on_plane(plane, x, y) for x, y in local)
    return AtomicNurbsCurve(control_points=points, weights=tuple(weights), knots=tuple(knots), degree=2)
