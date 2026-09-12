"""PointOriented - Create a point from plane {u,v,w} coordinates (Grasshopper "Point Oriented")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Planes import point_on_plane


class PointOriented(Component):
    """Create a point from plane {u,v,w} coordinates.

    Inputs:
        base_plane: Plane defining coordinate space (Grasshopper Base plane [item]).
        u_component: U parameter on plane (Grasshopper U component [item]).
        v_component: V parameter on plane (Grasshopper V component [item]).
        w_component: W parameter on plane (elevation) (Grasshopper W component [item]).

    Outputs:
        point: Oriented point coordinate (Grasshopper Point).

    Notes:
        Grasshopper: Vector > Point > Point Oriented (Pt).
        pyhopper decisions: none; ``origin + U x + V y + W z`` of the base plane, as in Grasshopper.
    """

    display_name = "Point Oriented"
    nickname = "Pt"
    gh_guid = "aa333235-5922-424c-9002-1e0b866a854b"

    inputs = [
        InputParam("base_plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("u_component", float, Access.ITEM, default=0.0),
        InputParam("v_component", float, Access.ITEM, default=0.0),
        InputParam("w_component", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
    ]

    def generate(self, base_plane=AtomicPlane.world_xy(), u_component=0.0, v_component=0.0, w_component=0.0):
        return point_on_plane(base_plane, float(u_component), float(v_component), float(w_component))
