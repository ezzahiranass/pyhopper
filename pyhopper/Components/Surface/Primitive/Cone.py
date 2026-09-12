"""Cone - Create an exact conical surface."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicSurface
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._helpers import circular_surface


class Cone(Component):
    """Create an exact conical side surface from a point or plane base."""

    inputs = [
        InputParam("base", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("radius", float, Access.ITEM, default=1.0),
        InputParam("length", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("cone", AtomicSurface),
        OutputParam("tip", AtomicPoint),
    ]

    def generate(self, base=AtomicPlane.world_xy(), radius=1.0, length=1.0):
        return circular_surface(base, radius, length, cone=True)
