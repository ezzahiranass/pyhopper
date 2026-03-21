"""Circle - Create a circle from a radius (and optional plane)."""

from pyhopper.Core.Atoms import AtomicCircle, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Circle(Component):
    """Create an ``AtomicCircle`` atom from a radius and an optional plane."""

    inputs = [
        InputParam("radius", float, Access.ITEM, default=1.0),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [OutputParam("circle")]

    def generate(self, radius=1.0, plane=AtomicPlane.world_xy()):
        return AtomicCircle(plane=plane, radius=float(radius))
