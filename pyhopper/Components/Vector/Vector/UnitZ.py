"""UnitZ - Returns a unit vector along the Z axis."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Component, OutputParam


class UnitZ(Component):
    """Return a unit vector along the world Z axis ``(0, 0, 1)``."""

    inputs = []
    outputs = [OutputParam("vector")]

    def generate(self):
        return AtomicVector.unit_z()