"""RadialGrid - 2D radial grid (Grasshopper "Radial")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._grids import radial_grid
from pyhopper.Core.TypeSystem import CURVE


class RadialGrid(Component):
    """2D radial grid.

    Inputs:
        plane: Base plane for grid (Grasshopper Plane [item]).
        size: Distance between concentric grid loops (Grasshopper Size [item]).
        extent_r: Number of grid cells in radial direction (Grasshopper Extent R [item]).
        extent_p: Number of grid cells in polar direction (Grasshopper Extent P [item]).

    Outputs:
        cells: Grid cell outlines (Grasshopper Cells).
        points: Points at grid nodes (Grasshopper Points).

    Notes:
        Grasshopper: Vector > Grid > Radial (RadGrid).
        pyhopper decisions: Grasshopper-verified layout — ``extent_p`` sectors per ring starting on
        the plane's y axis and running clockwise, the innermost ring made of triangles from the
        origin, cells grouped per ring (``extent_r`` branches) and points per ring (``extent_r +
        1`` branches, ring 0 being ``extent_p`` copies of the origin). Extents below 1 raise
        ``ValueError``.
    """

    display_name = "Radial"
    nickname = "RadGrid"
    gh_guid = "66eedc35-187d-4dab-b49b-408491b1255f"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("size", float, Access.ITEM, default=1.0),
        InputParam("extent_r", int, Access.ITEM, default=5),
        InputParam("extent_p", int, Access.ITEM, default=20),
    ]
    outputs = [
        OutputParam("cells", CURVE, access=Access.TREE),
        OutputParam("points", AtomicPoint, access=Access.TREE),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), size=1.0, extent_r=5, extent_p=20):
        cells, points = radial_grid(plane, size, extent_r, extent_p)
        return self.sub_branches(cells), self.sub_branches(points)
