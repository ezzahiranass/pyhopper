"""VectorXYZ - Construct a vector from XYZ scalar components."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class VectorXYZ(Component):
    """Construct an ``AtomicVector`` from X, Y, and Z scalar components."""

    inputs = [
        InputParam("x_component", float, Access.ITEM, default=0.0),
        InputParam("y_component", float, Access.ITEM, default=0.0),
        InputParam("z_component", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("vector", AtomicVector),
        OutputParam("length", float),
    ]

    def generate(self, x_component=0.0, y_component=0.0, z_component=0.0):
        vector = AtomicVector(float(x_component), float(y_component), float(z_component))
        return vector, vector.length
