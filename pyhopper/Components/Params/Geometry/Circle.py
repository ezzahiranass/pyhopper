"""Circle - Typed circle parameter container."""

from pyhopper.Core.Atoms import AtomicCircle
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Circle(Component):
    """Contain a DataTree of circle atoms."""

    inputs = [InputParam("circle", AtomicCircle, Access.ITEM)]
    outputs = [OutputParam("circle", AtomicCircle)]

    def generate(self, circle=None):
        return circle
