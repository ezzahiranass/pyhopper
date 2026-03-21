"""Move - Translate an object along a vector."""

from pyhopper.Core.Atoms import AtomicTransform, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform


class Move(Component):
    """Translate geometry along a motion vector.

    Accepts any geometry atom and a translation vector, returns the moved
    geometry and the corresponding transformation matrix.
    """

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("motion", AtomicVector, Access.ITEM, default=AtomicVector(0.0, 0.0, 0.0)),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, motion=AtomicVector(0.0, 0.0, 0.0)):
        xform = AtomicTransform.translation(motion)
        return apply_transform(xform, geometry), xform
