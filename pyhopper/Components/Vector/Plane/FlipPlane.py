"""FlipPlane - Flip or swap the axes of a plane (Grasshopper "Flip Plane")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Vectors import cross, negate


class FlipPlane(Component):
    """Flip or swap the axes of a plane.

    Inputs:
        plane: Plane to adjust (Grasshopper Plane [item]).
        reverse_x: Reverse the x-axis direction (Grasshopper Reverse X [item]).
        reverse_y: Reverse the y-axis direction (Grasshopper Reverse Y [item]).
        swap_axes: Swap the x and y axis directions (Grasshopper Swap axes [item]).

    Outputs:
        plane: Flipped plane (Grasshopper Plane).

    Notes:
        Grasshopper: Vector > Plane > Flip Plane (PFlip).
        pyhopper decisions: Grasshopper-verified order — reverse X, then reverse Y, then swap the
        axes; each reversal flips the normal and the swap flips it again. Defaults X and Y off,
        swap on (a plain flip).
    """

    display_name = "Flip Plane"
    nickname = "PFlip"
    gh_guid = "c73e1ed0-82a2-40b0-b4df-8f10e445d60b"

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("reverse_x", bool, Access.ITEM, default=False),
        InputParam("reverse_y", bool, Access.ITEM, default=False),
        InputParam("swap_axes", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), reverse_x=False, reverse_y=False, swap_axes=True):
        x_axis, y_axis = plane.x_axis, plane.y_axis
        if reverse_x:
            x_axis = negate(x_axis)
        if reverse_y:
            y_axis = negate(y_axis)
        if swap_axes:
            x_axis, y_axis = y_axis, x_axis
        return AtomicPlane(plane.origin, cross(x_axis, y_axis), x_axis)
