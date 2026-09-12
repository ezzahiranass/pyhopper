"""DeconstructBox - Deconstruct a box into its constituent parts (Grasshopper "Deconstruct Box")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBox, AtomicInterval, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Boxes import box_intervals


class DeconstructBox(Component):
    """Deconstruct a box into its constituent parts.

    Inputs:
        box: Base box (Grasshopper Box [item]).

    Outputs:
        plane: Box plane (Grasshopper Plane).
        x: {x} dimension of box (Grasshopper X).
        y: {y} dimension of box (Grasshopper Y).
        z: {z} dimension of box (Grasshopper Z).

    Notes:
        Grasshopper: Surface > Analysis > Deconstruct Box (DeBox).
        pyhopper decisions: pyhopper boxes are centred on their plane, so every domain is symmetric (+/- half a size);
        the plane and corners agree with Grasshopper.
    """

    display_name = "Deconstruct Box"
    nickname = "DeBox"
    gh_guid = "db7d83b1-2898-4ef9-9be5-4e94b4e2048d"

    inputs = [
        InputParam("box", AtomicBox, Access.ITEM),
    ]
    outputs = [
        OutputParam("plane", AtomicPlane),
        OutputParam("x", AtomicInterval),
        OutputParam("y", AtomicInterval),
        OutputParam("z", AtomicInterval),
    ]

    def generate(self, box=None):
        x, y, z = box_intervals(box)
        return box.plane, x, y, z
