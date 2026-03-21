"""UnitX - Returns a vector along the X axis scaled by a factor."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class UnitX(Component):
    """Return a vector along the world X axis scaled by *factor*."""

    inputs = [
        InputParam("factor", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("vector")]

    def generate(self, factor=1.0):
        f = float(factor)
        return AtomicVector(f, 0.0, 0.0)


