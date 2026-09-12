"""SurfaceClosestPoint - Find the closest point on a surface (Grasshopper "Surface Closest Point")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.ClosestPoints import surface_closest_point
from pyhopper.Core.TypeSystem import SURFACE


class SurfaceClosestPoint(Component):
    """Find the closest point on a surface.

    Inputs:
        point: Sample point (Grasshopper Point [item]).
        surface: Base surface (Grasshopper Surface [item]).

    Outputs:
        point: Closest point (Grasshopper Point).
        uv_point: {uv} coordinates of closest point (Grasshopper UV Point).
        distance: Distance between sample point and surface (Grasshopper Distance).

    Notes:
        Grasshopper: Surface > Analysis > Surface Closest Point (Srf CP).
        pyhopper decisions: Grasshopper-verified — the closest surface point (Newton from a sampled
        grid, boundary minima refined along the edges), the (u, v) parameters as a point and the
        distance.
    """

    display_name = "Surface Closest Point"
    nickname = "Srf CP"
    gh_guid = "4a9e9a8e-0943-4438-b360-129c30f2bb0f"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("surface", SURFACE, Access.ITEM),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("uv_point", AtomicPoint),
        OutputParam("distance", float),
    ]

    def generate(self, point=AtomicPoint.origin(), surface=None):
        u, v, closest, d, _ = surface_closest_point(surface, point)
        return closest, AtomicPoint(u, v, 0.0), d
