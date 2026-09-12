"""DeconstructRectangle - Retrieve the base plane and side intervals of a rectangle (Grasshopper "Deconstruct Rectangle")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicPlane, AtomicRectangle
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DeconstructRectangle(Component):
    """Retrieve the base plane and side intervals of a rectangle.

    Inputs:
        rectangle: Rectangle to deconstruct (Grasshopper Rectangle [item]).

    Outputs:
        base_plane: Base plane of rectangle (Grasshopper Base Plane).
        x_interval: Size interval along base plane X axis (Grasshopper X Interval).
        y_interval: Size interval along base plane Y axis (Grasshopper Y Interval).

    Notes:
        Grasshopper: Curve > Analysis > Deconstruct Rectangle (DRec).
        pyhopper decisions: none; the centred plane with symmetric X and Y intervals, as Grasshopper reports.
    """

    display_name = "Deconstruct Rectangle"
    nickname = "DRec"
    gh_guid = "e5c33a79-53d5-4f2b-9a97-d3d45c780edc"

    inputs = [
        InputParam("rectangle", AtomicRectangle, Access.ITEM),
    ]
    outputs = [
        OutputParam("base_plane", AtomicPlane),
        OutputParam("x_interval", AtomicInterval),
        OutputParam("y_interval", AtomicInterval),
    ]

    def generate(self, rectangle=None):
        half_x, half_y = float(rectangle.x_size) / 2.0, float(rectangle.y_size) / 2.0
        return rectangle.plane, AtomicInterval(-half_x, half_x), AtomicInterval(-half_y, half_y)
