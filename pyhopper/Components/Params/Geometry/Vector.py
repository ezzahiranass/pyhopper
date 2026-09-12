"""Vector - Typed vector parameter container."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Vector(Component):
    """Contain and normalize a DataTree of vector values."""

    inputs = [InputParam("vector", AtomicVector, Access.ITEM)]
    outputs = [OutputParam("vector", AtomicVector)]

    def generate(self, vector=None):
        return vector
