"""VectorLength - Measure the length of a vector."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class VectorLength(Component):
    """Measure the Euclidean length of an ``AtomicVector``."""

    inputs = [InputParam("vector", AtomicVector, Access.ITEM)]
    outputs = [OutputParam("length", float)]

    def generate(self, vector=None):
        return vector.length
