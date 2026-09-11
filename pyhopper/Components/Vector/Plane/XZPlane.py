"""XZPlane - Create a world XZ plane at an origin."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class XZPlane(Component):
    """Create a world XZ plane centered at an origin point."""

    inputs = [InputParam("origin", AtomicPoint, Access.ITEM, default=AtomicPoint.origin())]
    outputs = [OutputParam("plane", AtomicPlane)]

    def generate(self, origin=AtomicPoint.origin()):
        return AtomicPlane(
            origin=origin,
            normal=AtomicVector(0.0, -1.0, 0.0),
            x_axis=AtomicVector.unit_x(),
        )
