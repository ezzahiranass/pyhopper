"""PlaneCoordinates - Get the coordinates of a point in a plane axis system (Grasshopper "Plane Coordinates")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Planes import plane_coordinates


class PlaneCoordinates(Component):
    """Get the coordinates of a point in a plane axis system.

    Inputs:
        point: Input point (Grasshopper Point [item]).
        system: Local coordinate system (Grasshopper System [item]).

    Outputs:
        x_coordinate: Point {x} coordinate (Grasshopper X coordinate).
        y_coordinate: Point {y} coordinate (Grasshopper Y coordinate).
        z_coordinate: Point {z} coordinate (Grasshopper Z coordinate).

    Notes:
        Grasshopper: Vector > Plane > Plane Coordinates (PlCoord).
        pyhopper decisions: none; the point's coordinates in the system plane (x, y along the axes, z along the normal).
    """

    display_name = "Plane Coordinates"
    nickname = "PlCoord"
    gh_guid = "5f127fa4-ca61-418e-bb2d-e3739d900f1f"

    inputs = [
        InputParam("point", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("system", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("x_coordinate", float),
        OutputParam("y_coordinate", float),
        OutputParam("z_coordinate", float),
    ]

    def generate(self, point=AtomicPoint.origin(), system=AtomicPlane.world_xy()):
        return plane_coordinates(system, point)
