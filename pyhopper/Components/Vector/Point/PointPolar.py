"""PointPolar - Create a point from polar {phi,theta,offset} coordinates (Grasshopper "Point Polar")."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Planes import point_on_plane


class PointPolar(Component):
    """Create a point from polar {phi,theta,offset} coordinates.

    Inputs:
        base_plane: Plane defining polar coordinate space (Grasshopper Base plane [item]).
        xy_angle: Angle in radians for P(x,y) rotation (Grasshopper XY angle [item]).
        z_angle: Angle in radians for P(z) rotation (Grasshopper Z angle [item]).
        offset: Offset distance for point (Grasshopper Offset [item]).

    Outputs:
        point: Polar point coordinate (Grasshopper Point).

    Notes:
        Grasshopper: Vector > Point > Point Polar (Pt).
        pyhopper decisions: ``xy_angle`` turns from the plane's x axis, ``z_angle`` lifts towards the normal,
        both in radians; Grasshopper default ``offset = 1``.
    """

    display_name = "Point Polar"
    nickname = "Pt"
    gh_guid = "a435f5c8-28a2-43e8-a52a-0b6e73c2e300"

    inputs = [
        InputParam("base_plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("xy_angle", float, Access.ITEM, default=0.0),
        InputParam("z_angle", float, Access.ITEM, default=0.0),
        InputParam("offset", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
    ]

    def generate(self, base_plane=AtomicPlane.world_xy(), xy_angle=0.0, z_angle=0.0, offset=1.0):
        radius = float(offset) * math.cos(float(z_angle))
        return point_on_plane(base_plane, radius * math.cos(float(xy_angle)), radius * math.sin(float(xy_angle)), float(offset) * math.sin(float(z_angle)))
