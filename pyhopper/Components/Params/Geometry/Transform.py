"""Transform - Typed transform parameter container."""

from pyhopper.Core.Atoms import AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Transform(Component):
    """Contain a DataTree of affine transform atoms."""

    inputs = [InputParam("transform", AtomicTransform, Access.ITEM)]
    outputs = [OutputParam("transform", AtomicTransform)]

    def generate(self, transform=None):
        return transform
