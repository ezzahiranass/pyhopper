"""BoxRectangle - Create a box defined by a rectangle and a height (Grasshopper "Box Rectangle")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBox, AtomicInterval, AtomicRectangle
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Utils.Vectors import translate


class BoxRectangle(Component):
    """Create a box defined by a rectangle and a height.

    Inputs:
        rectangle: Base rectangle (Grasshopper Rectangle [item]).
        height: Box height (Grasshopper Height [item]).

    Outputs:
        box: Resulting box (Grasshopper Box).

    Notes:
        Grasshopper: Surface > Primitive > Box Rectangle (BoxRec).
        pyhopper decisions: none; the box stands on the rectangle's plane over the height domain
        (centred box, height default 0 to 10 as in Grasshopper).
    """

    display_name = "Box Rectangle"
    nickname = "BoxRec"
    gh_guid = "d0a56c9e-2483-45e7-ab98-a450b97f1bc0"

    inputs = [
        InputParam("rectangle", AtomicRectangle, Access.ITEM),
        InputParam("height", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 10.0)),
    ]
    outputs = [
        OutputParam("box", AtomicBox),
    ]

    def generate(self, rectangle=None, height=AtomicInterval(0.0, 10.0)):
        low, high = float(height.start), float(height.end)
        plane = rectangle.plane
        centre = translate(plane.origin, plane.normal, 0.5 * (low + high))
        return AtomicBox(AtomicPlane(centre, plane.normal, plane.x_axis), float(rectangle.x_size), float(rectangle.y_size), abs(high - low))
