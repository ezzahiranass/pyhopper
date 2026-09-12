"""Line - Typed line parameter container."""

from pyhopper.Core.Atoms import AtomicLine
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Line(Component):
    """Contain a DataTree of line atoms."""

    inputs = [InputParam("line", AtomicLine, Access.ITEM)]
    outputs = [OutputParam("line", AtomicLine)]

    def generate(self, line=None):
        return line
