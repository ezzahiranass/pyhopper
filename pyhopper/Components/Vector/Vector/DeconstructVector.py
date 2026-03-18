"""DeconstructVector - Split a vector into its XYZ components."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DeconstructVector(Component):
    """Split an ``AtomicVector`` into X, Y, and Z scalar components."""

    inputs = [InputParam("vector", AtomicVector, Access.ITEM)]
    outputs = [
        OutputParam("x_component", float),
        OutputParam("y_component", float),
        OutputParam("z_component", float),
    ]

    def generate(self, vector=None):
        return float(vector.x), float(vector.y), float(vector.z)
