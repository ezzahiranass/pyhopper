"""Rectangle - Typed rectangle parameter container."""

from pyhopper.Core.Atoms import AtomicRectangle
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Rectangle(Component):
    """Contain a DataTree of rectangle atoms."""

    inputs = [InputParam("rectangle", AtomicRectangle, Access.ITEM)]
    outputs = [OutputParam("rectangle", AtomicRectangle)]

    def generate(self, rectangle=None):
        return rectangle
