"""Bounds - Create a numeric domain encompassing a list of numbers."""

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Bounds(Component):
    """Return the numeric domain between the lowest and highest branch values."""

    inputs = [InputParam("numbers", float, Access.LIST)]
    outputs = [OutputParam("domain", AtomicInterval)]

    def generate(self, numbers=None):
        if not numbers:
            raise ValueError("Bounds requires at least one number")
        values = [float(number) for number in numbers]
        return AtomicInterval(min(values), max(values))
