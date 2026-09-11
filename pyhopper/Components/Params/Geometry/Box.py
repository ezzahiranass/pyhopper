"""Box - Typed box parameter container."""

from pyhopper.Core.Atoms import AtomicBox
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Box(Component):
    """Contain a DataTree of named box atoms."""

    inputs = [InputParam("box", AtomicBox, Access.ITEM)]
    outputs = [OutputParam("box", AtomicBox)]

    def generate(self, box=None):
        return box
