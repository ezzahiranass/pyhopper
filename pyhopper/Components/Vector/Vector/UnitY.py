"""UnitY - Returns a vector along the Y axis scaled by a factor."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class UnitY(Component):
    """Return a vector along the world Y axis scaled by *factor*."""

    inputs = [
        InputParam("factor", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("vector")]

    def generate(self, factor=1.0):
        f = float(factor)
        return AtomicVector(0.0, f, 0.0)