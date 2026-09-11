"""Rectangle - Create a rectangle from plane and side lengths."""

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import GEOMETRY

from ._rectangles import make_rectangle


class Rectangle(Component):
    """Create an ``AtomicRectangle`` from a plane and side lengths.

    Returns a named rectangle and its perimeter length. A non-zero radius
    (clamped to half the shorter side) produces the exact rational degree-2
    fillet curve Grasshopper builds, shared with ``Rectangle2Pt``.
    """

    inputs = [
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("x_size", float, Access.ITEM, default=1.0),
        InputParam("y_size", float, Access.ITEM, default=1.0),
        InputParam("radius", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("rectangle", GEOMETRY),
        OutputParam("length", float),
    ]

    def generate(self, plane=AtomicPlane.world_xy(), x_size=1.0, y_size=1.0, radius=0.0):
        return make_rectangle(plane, x_size, y_size, radius)
