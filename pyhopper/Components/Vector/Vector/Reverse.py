"""Reverse - Reverse the direction of a vector."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Reverse(Component):
    """Reverse the direction of an ``AtomicVector``."""

    inputs = [InputParam("vector", AtomicVector, Access.ITEM)]
    outputs = [OutputParam("vector", AtomicVector)]

    def generate(self, vector=None):
        return AtomicVector(-vector.x, -vector.y, -vector.z)
