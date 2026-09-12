"""Grid construction shared by the Vector › Grid components.

Layouts verified against Grasshopper 8. Rectangular / square: the first grid
corner sits on the plane origin, points are grouped per column
(``extent_x + 1`` columns of ``extent_y + 1`` points along the plane's y axis)
and cells per column (``extent_x`` columns of ``extent_y`` rectangles centred
in their cell). Hexagonal: flat-topped hexagons of circumradius ``size`` in
columns ``1.5 * size`` apart, odd columns raised by half a row, points are the
cell centres. Triangular: equilateral triangles of edge ``size`` whose
orientation alternates with ``column + row``, points are the centroids. Radial:
``extent_p`` sectors per ring starting at the plane's y axis and running
clockwise, ring 0 made of triangles from the origin, points per ring (ring 0 is
``extent_p`` copies of the origin).
"""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicPolyline, AtomicRectangle
from pyhopper.Utils.Planes import point_on_plane


def checked_extent(value: int, name: str) -> int:
    extent = int(value)
    if extent < 1:
        raise ValueError(f"Grid extent {name} cannot be less than 1")
    return extent


def rectangular_grid(
    plane: AtomicPlane,
    size_x: float,
    size_y: float,
    extent_x: int,
    extent_y: int,
) -> tuple[list[list[AtomicRectangle]], list[list[AtomicPoint]]]:
    """``(cell columns, point columns)`` of a rectangular grid anchored at the plane origin."""
    columns = checked_extent(extent_x, "X")
    rows = checked_extent(extent_y, "Y")
    width, height = float(size_x), float(size_y)
    points = [[point_on_plane(plane, column * width, row * height) for row in range(rows + 1)] for column in range(columns + 1)]
    cells = []
    for column in range(columns):
        cells.append(
            [
                AtomicRectangle(
                    AtomicPlane(point_on_plane(plane, (column + 0.5) * width, (row + 0.5) * height), plane.normal, plane.x_axis),
                    width,
                    height,
                )
                for row in range(rows)
            ]
        )
    return cells, points


def _closed(points: list[AtomicPoint]) -> AtomicPolyline:
    return AtomicPolyline(tuple(points + [points[0]]))


def hexagonal_grid(plane: AtomicPlane, size: float, extent_x: int, extent_y: int) -> tuple[list[list[AtomicPolyline]], list[list[AtomicPoint]]]:
    """``(cell columns, centre columns)`` of a hexagonal grid; ``size`` is the circumradius."""
    columns = checked_extent(extent_x, "X")
    rows = checked_extent(extent_y, "Y")
    radius = float(size)
    row_height = radius * math.sqrt(3.0)
    cells, points = [], []
    for column in range(columns):
        cx = column * 1.5 * radius
        lift = row_height / 2.0 if column % 2 else 0.0
        cell_column, point_column = [], []
        for row in range(rows):
            cy = row * row_height + lift
            point_column.append(point_on_plane(plane, cx, cy))
            corners = [
                point_on_plane(plane, cx + radius * math.cos(k * math.pi / 3.0), cy + radius * math.sin(k * math.pi / 3.0))
                for k in range(6)
            ]
            cell_column.append(_closed(corners))
        cells.append(cell_column)
        points.append(point_column)
    return cells, points


def triangular_grid(plane: AtomicPlane, size: float, extent_x: int, extent_y: int) -> tuple[list[list[AtomicPolyline]], list[list[AtomicPoint]]]:
    """``(cell columns, centroid columns)`` of a triangular grid; ``size`` is the edge length."""
    columns = checked_extent(extent_x, "X")
    rows = checked_extent(extent_y, "Y")
    edge = float(size)
    height = edge * math.sqrt(3.0) / 2.0
    cells, points = [], []
    for column in range(columns):
        x0 = column * edge / 2.0
        cell_column, point_column = [], []
        for row in range(rows):
            y0 = row * height
            if (column + row) % 2 == 0:  # pointing up: base at y0, apex above
                corners = [point_on_plane(plane, x0, y0), point_on_plane(plane, x0 + edge, y0), point_on_plane(plane, x0 + edge / 2.0, y0 + height)]
                centroid = point_on_plane(plane, x0 + edge / 2.0, y0 + height / 3.0)
            else:  # pointing down: vertex at y0, edge above
                corners = [point_on_plane(plane, x0 + edge / 2.0, y0), point_on_plane(plane, x0 + edge, y0 + height), point_on_plane(plane, x0, y0 + height)]
                centroid = point_on_plane(plane, x0 + edge / 2.0, y0 + 2.0 * height / 3.0)
            cell_column.append(_closed(corners))
            point_column.append(centroid)
        cells.append(cell_column)
        points.append(point_column)
    return cells, points


def radial_grid(plane: AtomicPlane, size: float, extent_r: int, extent_p: int) -> tuple[list[list[AtomicPolyline]], list[list[AtomicPoint]]]:
    """``(cell rings, point rings)`` of a radial grid; ``size`` is the ring spacing."""
    rings = checked_extent(extent_r, "R")
    sectors = checked_extent(extent_p, "P")
    step = float(size)

    def at(ring: int, sector: int) -> AtomicPoint:
        angle = math.pi / 2.0 - sector * 2.0 * math.pi / sectors  # start on the y axis, run clockwise
        return point_on_plane(plane, ring * step * math.cos(angle), ring * step * math.sin(angle))

    cells = []
    for ring in range(rings):
        ring_cells = []
        for sector in range(sectors):
            if ring == 0:
                corners = [at(0, 0), at(1, sector), at(1, sector + 1)]
            else:
                corners = [at(ring, sector), at(ring + 1, sector), at(ring + 1, sector + 1), at(ring, sector + 1)]
            ring_cells.append(_closed(corners))
        cells.append(ring_cells)
    points = [[at(ring, sector) for sector in range(sectors)] for ring in range(rings + 1)]
    return cells, points
