"""YZPlane - Create a world YZ plane at an origin."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class YZPlane(Component):
    """Create a world YZ plane centered at an origin point."""

    inputs = [InputParam("origin", AtomicPoint, Access.ITEM, default=AtomicPoint.origin())]
    outputs = [OutputParam("plane", AtomicPlane)]

    def generate(self, origin=AtomicPoint.origin()):
        return AtomicPlane(origin=origin, normal=AtomicVector.unit_x(), x_axis=AtomicVector.unit_y())
