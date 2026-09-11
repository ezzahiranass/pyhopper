"""Cylinder - Create an exact cylindrical surface."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicSurface
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._helpers import circular_surface


class Cylinder(Component):
    """Create an exact cylindrical side surface from a point or plane base."""

    inputs = [
        InputParam("base", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("radius", float, Access.ITEM, default=1.0),
        InputParam("length", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("cylinder", AtomicSurface)]

    def generate(self, base=AtomicPlane.world_xy(), radius=1.0, length=1.0):
        surface, _ = circular_surface(base, radius, length)
        return surface
