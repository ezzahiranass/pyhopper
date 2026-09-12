"""PointCylindrical - Create a point from cylindrical {angle,radius,elevation} coordinates (Grasshopper "Point Cylindrical")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math

from pyhopper.Utils.Planes import point_on_plane


class PointCylindrical(Component):
    """Create a point from cylindrical {angle,radius,elevation} coordinates.

    Inputs:
        base_plane: Plane defining cylindrical coordinate space (Grasshopper Base plane [item]).
        angle: Angle in radians for P(x,y) rotation (Grasshopper Angle [item]).
        radius: Radius of cylinder (Grasshopper Radius [item]).
        elevation: Elevation of point (Grasshopper Elevation [item]).

    Outputs:
        point: Cylindrical point coordinate (Grasshopper Point).

    Notes:
        Grasshopper: Vector > Point > Point Cylindrical (Pt).
        pyhopper decisions: ``origin + R cos(A) x + R sin(A) y + E z`` with A in radians; defaults 0, 1, 0 as in Grasshopper.
    """

    display_name = "Point Cylindrical"
    nickname = "Pt"
    gh_guid = "23603075-be64-4d86-9294-c3c125a12104"

    inputs = [
        InputParam("base_plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("angle", float, Access.ITEM, default=0.0),
        InputParam("radius", float, Access.ITEM, default=1.0),
        InputParam("elevation", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
    ]

    def generate(self, base_plane=AtomicPlane.world_xy(), angle=0.0, radius=1.0, elevation=0.0):
        r, a = float(radius), float(angle)
        return point_on_plane(base_plane, r * math.cos(a), r * math.sin(a), float(elevation))
