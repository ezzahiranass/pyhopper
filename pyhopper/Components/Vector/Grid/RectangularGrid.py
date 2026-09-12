"""RectangularGrid - 2D grid with rectangular cells (Grasshopper "Rectangular")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicRectangle
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._grids import rectangular_grid


class RectangularGrid(Component):
    """2D grid with rectangular cells.

    Inputs:
        plane: Base plane for grid (Grasshopper Plane [item]).
        size_x: Size of grid cells in base plane x-direction (Grasshopper Size X [item]).
        size_y: Size of grid cells in base plane y-direction (Grasshopper Size Y [item]).
        extent_x: Number of grid cells in base plane x direction (Grasshopper Extent X [item]).
        extent_y: Number of grid cells in base plane y direction (Grasshopper Extent Y [item]).

    Outputs:
        cells: Grid cell outlines (Grasshopper Cells).
        points: Points at grid corners (Grasshopper Points).

    Notes:
        Grasshopper: Vector > Grid > Rectangular (RecGrid).
        pyhopper decisions: the first corner sits on the plane origin; ``points`` holds ``extent_x + 1`` columns
        of ``extent_y + 1`` points and ``cells`` ``extent_x`` columns of ``extent_y`` centred
        rectangles, each column a sub-branch ``{path;iteration;column}`` exactly as Grasshopper
        lays them out; extents below 1 raise ``ValueError``. Grasshopper defaults 1 / 2 / 10 / 5.
    """

    display_name = "Rectangular"
    nickname = "RecGrid"
    gh_guid = "1a25aae0-0b56-497a-85b2-cc5bf7e4b96b"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("size_x", float, Access.ITEM, default=1.0),
        InputParam("size_y", float, Access.ITEM, default=2.0),
        InputParam("extent_x", int, Access.ITEM, default=10),
        InputParam("extent_y", int, Access.ITEM, default=5),
    ]
    outputs = [
        OutputParam("cells", AtomicRectangle),
        OutputParam("points", AtomicPoint, access=Access.TREE),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), size_x=1.0, size_y=2.0, extent_x=10, extent_y=5):
        cells, points = rectangular_grid(plane, size_x, size_y, extent_x, extent_y)
        return self.sub_branches(cells), self.sub_branches(points)
