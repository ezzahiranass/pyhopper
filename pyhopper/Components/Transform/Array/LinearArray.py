"""LinearArray - Array geometry along a direction vector."""

from pyhopper.Core.Atoms import AtomicTransform, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._helpers import array_result, checked_count, scaled_vector


class LinearArray(Component):
    """Create a linear array using the direction vector as the item interval."""

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("direction", AtomicVector, Access.ITEM, default=AtomicVector.unit_x()),
        InputParam("count", int, Access.ITEM, default=10),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, direction=AtomicVector.unit_x(), count=10):
        transforms = [
            AtomicTransform.translation(scaled_vector(direction, index))
            for index in range(checked_count(count))
        ]
        return array_result(geometry, transforms)
