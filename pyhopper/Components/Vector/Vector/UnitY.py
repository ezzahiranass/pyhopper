"""UnitY - Returns a unit vector along the Y axis."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Component, OutputParam

class UnitY(Component):
    """Return a unit vector along the world Y axis ``(0, 1, 0)``."""

    inputs = []
    outputs = [OutputParam("vector")]

    def generate(self):
        return AtomicVector.unit_y()