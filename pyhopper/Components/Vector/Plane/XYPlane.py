"""XYPlane - Create a world XY plane at an origin."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class XYPlane(Component):
    """Create a world XY plane centered at an origin point."""

    inputs = [InputParam("origin", AtomicPoint, Access.ITEM, default=AtomicPoint.origin())]
    outputs = [OutputParam("plane", AtomicPlane)]

    def generate(self, origin=AtomicPoint.origin()):
        return AtomicPlane(origin=origin, normal=AtomicVector.unit_z(), x_axis=AtomicVector.unit_x())
