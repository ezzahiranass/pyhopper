"""TriangularGrid - 2D grid with triangular cells (Grasshopper "Triangular")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._grids import triangular_grid
from pyhopper.Core.TypeSystem import CURVE


class TriangularGrid(Component):
    """2D grid with triangular cells.

    Inputs:
        plane: Base plane for grid (Grasshopper Plane [item]).
        size: Size of triangle edges (Grasshopper Size [item]).
        extent_x: Number of grid cells in base plane x directions (Grasshopper Extent X [item]).
        extent_y: Number of grid cells in base plane y directions (Grasshopper Extent Y [item]).

    Outputs:
        cells: Grid cell outlines (Grasshopper Cells).
        points: Points at grid centers (Grasshopper Points).

    Notes:
        Grasshopper: Vector > Grid > Triangular (TriGrid).
        pyhopper decisions: Grasshopper-verified layout — equilateral triangles of edge ``size``
        in columns half an edge apart, pointing up when ``column + row`` is even and down otherwise,
        cells and centroids grouped per column. Extents below 1 raise ``ValueError``.
    """

    display_name = "Triangular"
    nickname = "TriGrid"
    gh_guid = "86a9944b-dea5-4126-9433-9e95ff07927a"

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
        cells, points = triangular_grid(plane, size, extent_x, extent_y)
        return self.sub_branches(cells), self.sub_branches(points)
