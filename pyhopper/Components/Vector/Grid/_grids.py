"""Grid construction shared by the Vector › Grid components.

Layout verified against Grasshopper 8: the first grid corner sits on the plane
origin, points are grouped per column (``extent_x + 1`` columns of
``extent_y + 1`` points along the plane's y axis) and cells per column
(``extent_x`` columns of ``extent_y`` rectangles centred in their cell).
"""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicRectangle
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
