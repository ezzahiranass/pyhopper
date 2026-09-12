"""HexagonalGrid - 2D grid with hexagonal cells (Grasshopper "Hexagonal")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._grids import hexagonal_grid
from pyhopper.Core.TypeSystem import CURVE


class HexagonalGrid(Component):
    """2D grid with hexagonal cells.

    Inputs:
        plane: Base plane for grid (Grasshopper Plane [item]).
        size: Size of hexagon radius (Grasshopper Size [item]).
        extent_x: Number of grid cells in base plane x directions (Grasshopper Extent X [item]).
        extent_y: Number of grid cells in base plane y directions (Grasshopper Extent Y [item]).

    Outputs:
        cells: Grid cell outlines (Grasshopper Cells).
        points: Points at grid centers (Grasshopper Points).

    Notes:
        Grasshopper: Vector > Grid > Hexagonal (HexGrid).
        pyhopper decisions: Grasshopper-verified layout — flat-topped hexagons of circumradius
        ``size``, columns ``1.5 × size`` apart with odd columns raised half a row, cells and centre
        points grouped per column (``extent_x`` branches of ``extent_y``). Extents below 1 raise
        ``ValueError``.
    """

    display_name = "Hexagonal"
    nickname = "HexGrid"
    gh_guid = "125dc122-8544-4617-945e-bb9a0c101c50"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("size", float, Access.ITEM, default=1.0),
        InputParam("extent_x", int, Access.ITEM, default=5),
        InputParam("extent_y", int, Access.ITEM, default=5),
    ]
    outputs = [
        OutputParam("cells", CURVE, access=Access.TREE),
        OutputParam("points", AtomicPoint, access=Access.TREE),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), size=1.0, extent_x=5, extent_y=5):
        cells, points = hexagonal_grid(plane, size, extent_x, extent_y)
        return self.sub_branches(cells), self.sub_branches(points)
