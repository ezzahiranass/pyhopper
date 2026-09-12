"""SurfaceFromPoints - Create a nurbs surface from a grid of points (Grasshopper "Surface From Points")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.SurfaceBuilders import surface_from_grid
from pyhopper.Core.TypeSystem import SURFACE


class SurfaceFromPoints(Component):
    """Create a nurbs surface from a grid of points.

    Inputs:
        points: Grid of points (Grasshopper Points [list]).
        u_count: Number of points in {u} direction (Grasshopper U Count [item]).
        interpolate: Interpolate samples (Grasshopper Interpolate [item]).

    Outputs:
        surface: Resulting surface (Grasshopper Surface).

    Notes:
        Grasshopper: Surface > Freeform > Surface From Points (SrfGrid).
        pyhopper decisions: Grasshopper's grid convention — the list holds ``u_count`` runs of
        consecutive points, each run being one U column (``poles[v][u] = points[u * v_count + v]``);
        degrees are ``min(3, count - 1)`` per direction. ``interpolate`` fits the surface through the
        points with averaged chord-length parameters (matches Grasshopper's knots and poles); a point
        count that is not a multiple of ``u_count`` raises ``ValueError``.
    """

    display_name = "Surface From Points"
    nickname = "SrfGrid"
    gh_guid = "4b04a1e1-cddf-405d-a7db-335aaa940541"

    inputs = [
        InputParam("points", AtomicPoint, Access.LIST),
        InputParam("u_count", int, Access.ITEM),
        InputParam("interpolate", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("surface", SURFACE),
    ]

    def generate(self, points=None, u_count=None, interpolate=False):
        items = list(points or [])
        columns = int(u_count)
        if columns < 2 or len(items) % columns:
            raise ValueError("SurfaceFromPoints needs a point count that is a multiple of u_count (at least 2)")
        rows = len(items) // columns
        grid = [[items[u * rows + v] for u in range(columns)] for v in range(rows)]
        return surface_from_grid(grid, bool(interpolate))
