"""UnitX - Returns a unit vector along the X axis."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Component, OutputParam

class UnitX(Component):
    """Return a unit vector along the world X axis ``(1, 0, 0)``."""

    inputs = []
    outputs = [OutputParam("vector")]

    def generate(self):
        return AtomicVector.unit_x()


