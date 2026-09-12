"""SquareGrid - 2D grid with square cells (Grasshopper "Square")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicRectangle
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._grids import rectangular_grid


class SquareGrid(Component):
    """2D grid with square cells.

    Inputs:
        plane: Base plane for grid (Grasshopper Plane [item]).
        size: Size of grid cells (Grasshopper Size [item]).
        extent_x: Number of grid cells in base plane x direction (Grasshopper Extent X [item]).
        extent_y: Number of grid cells in base plane y direction (Grasshopper Extent Y [item]).

    Outputs:
        cells: Grid cell outlines (Grasshopper Cells).
        points: Points at grid corners (Grasshopper Points).

    Notes:
        Grasshopper: Vector > Grid > Square (SqGrid).
        pyhopper decisions: a rectangular grid with equal cell sides: the first corner sits on the plane origin,
        ``points`` holds ``extent_x + 1`` columns of ``extent_y + 1`` points and ``cells``
        ``extent_x`` columns of ``extent_y`` centred squares, each column a sub-branch
        ``{path;iteration;column}`` like Grasshopper; extents below 1 raise ``ValueError``.
        Grasshopper defaults 1 / 5 / 5.
    """

    display_name = "Square"
    nickname = "SqGrid"
    gh_guid = "717a1e25-a075-4530-bc80-d43ecc2500d9"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("size", float, Access.ITEM, default=1.0),
        InputParam("extent_x", int, Access.ITEM, default=5),
        InputParam("extent_y", int, Access.ITEM, default=5),
    ]
    outputs = [
        OutputParam("cells", AtomicRectangle),
        OutputParam("points", AtomicPoint, access=Access.TREE),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), size=1.0, extent_x=5, extent_y=5):
        cells, points = rectangular_grid(plane, size, size, extent_x, extent_y)
        return self.sub_branches(cells), self.sub_branches(points)
