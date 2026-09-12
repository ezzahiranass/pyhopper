"""PlaneClosestPoint - Find the closest point on a plane (Grasshopper "Plane Closest Point")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Planes import plane_coordinates, project_point


class PlaneClosestPoint(Component):
    """Find the closest point on a plane.

    Inputs:
        point: Sample point (Grasshopper Point [item]).
        plane: Projection plane (Grasshopper Plane [item]).

    Outputs:
        point: Projected point (Grasshopper Point).
        uv_point: {uv} coordinates of projected point (Grasshopper UV Point).
        distance: Signed distance between point and plane (Grasshopper Distance).

    Notes:
        Grasshopper: Vector > Plane > Plane Closest Point (CP).
        pyhopper decisions: ``uv_point`` carries the plane coordinates as ``(u, v, 0)`` and
        ``distance`` is signed along the normal (positive on the normal's side), as in Grasshopper.
    """

    display_name = "Plane Closest Point"
    nickname = "CP"
    gh_guid = "b075c065-efda-4c9f-9cc9-288362b1b4b9"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("uv_point", AtomicPoint),
        OutputParam("distance", float),
    ]

    def generate(self, point=AtomicPoint.origin(), plane=AtomicPlane.world_xy()):
        x, y, z = plane_coordinates(plane, point)
        return project_point(plane, point), AtomicPoint(x, y, 0.0), z
