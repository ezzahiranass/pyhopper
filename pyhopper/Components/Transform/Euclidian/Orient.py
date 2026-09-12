"""Orient - Reorient geometry from one plane to another."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform


class Orient(Component):
    """Apply a plane-to-plane change-of-basis transform to geometry."""

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("source", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("target", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(
        self,
        geometry=None,
        source=AtomicPlane.world_xy(),
        target=AtomicPlane.world_xy(),
    ):
        xform = AtomicTransform.orient(source, target)
        return apply_transform(xform, geometry), xform
