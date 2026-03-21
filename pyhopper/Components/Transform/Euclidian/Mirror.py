"""Mirror - Mirror an object across a plane."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform


class Mirror(Component):
    """Reflect geometry across a mirror plane.

    Accepts any geometry atom and a plane, returns the mirrored geometry
    and the corresponding transformation matrix.
    """

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_yz()),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, plane=AtomicPlane.world_yz()):
        xform = AtomicTransform.reflection(plane)
        return apply_transform(xform, geometry), xform
