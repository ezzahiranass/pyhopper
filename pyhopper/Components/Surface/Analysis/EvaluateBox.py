"""EvaluateBox - Evaluate a box in normalised {UVW} space (Grasshopper "Evaluate Box")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBox, AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Planes import point_on_plane


class EvaluateBox(Component):
    """Evaluate a box in normalised {UVW} space.

    Inputs:
        box: Base box (Grasshopper Box [item]).
        u_parameter: {u} parameter (values between 0.0 and 1.0 are inside the box) (Grasshopper U parameter [item]).
        v_parameter: {v} parameter (values between 0.0 and 1.0 are inside the box) (Grasshopper V parameter [item]).
        w_parameter: {w} parameter (values between 0.0 and 1.0 are inside the box) (Grasshopper W parameter [item]).

    Outputs:
        plane: Plane at {uvw} coordinate (Grasshopper Plane).
        point: Point at {uvw} coordinate (Grasshopper Point).
        include: True if point is inside or on box (Grasshopper Include).

    Notes:
        Grasshopper: Surface > Analysis > Evaluate Box (Box).
        pyhopper decisions: none; the parameters run 0..1 across each side, the plane carries the
        box's orientation at the point and ``include`` says whether all three parameters lie in
        [0, 1]. Defaults 0.5 as in Grasshopper.
    """

    display_name = "Evaluate Box"
    nickname = "Box"
    gh_guid = "13b40e9c-3aed-4669-b2e8-60bd02091421"

    inputs = [
        InputParam("box", AtomicBox, Access.ITEM),
        InputParam("u_parameter", float, Access.ITEM, default=0.5),
        InputParam("v_parameter", float, Access.ITEM, default=0.5),
        InputParam("w_parameter", float, Access.ITEM, default=0.5),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
        OutputParam("point", AtomicPoint),
        OutputParam("include", bool),
    ]

    def generate(self, box=None, u_parameter=0.5, v_parameter=0.5, w_parameter=0.5):
        u, v, w = float(u_parameter), float(v_parameter), float(w_parameter)
        point = point_on_plane(box.plane, (u - 0.5) * float(box.x_size), (v - 0.5) * float(box.y_size), (w - 0.5) * float(box.z_size))
        inside = all(0.0 <= t <= 1.0 for t in (u, v, w))
        return AtomicPlane(point, box.plane.normal, box.plane.x_axis), point, inside
