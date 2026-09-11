"""CenterBox - Create a box centered on a point or plane."""

from pyhopper.Core.Atoms import AtomicBox, AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._helpers import centered_box


class CenterBox(Component):
    """Create a named box centered on a point or plane base."""

    inputs = [
        InputParam("base", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("x_size", float, Access.ITEM, default=1.0),
        InputParam("y_size", float, Access.ITEM, default=1.0),
        InputParam("z_size", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("box", AtomicBox)]

    def generate(self, base=AtomicPlane.world_xy(), x_size=1.0, y_size=1.0, z_size=1.0):
        return centered_box(base, x_size, y_size, z_size)
