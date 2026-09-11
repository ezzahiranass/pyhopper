"""Scale - Uniformly scale geometry around a center point."""

from pyhopper.Core.Atoms import AtomicPoint, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform


class Scale(Component):
    """Uniformly scale geometry and return the applied transform."""

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("center", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("factor", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, center=AtomicPoint.origin(), factor=1.0):
        xform = AtomicTransform.scale(center, float(factor))
        return apply_transform(xform, geometry), xform
