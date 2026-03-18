"""Amplitude - Set the amplitude of a vector."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Amplitude(Component):
    """Set a vector's amplitude while preserving its direction."""

    inputs = [
        InputParam("vector", AtomicVector, Access.ITEM),
        InputParam("amplitude", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("vector", AtomicVector)]

    def generate(self, vector=None, amplitude=1.0):
        direction = vector.unitize()
        scale = float(amplitude)
        return AtomicVector(direction.x * scale, direction.y * scale, direction.z * scale)
