"""RectangularArray - Array geometry in a rectangular cell grid."""

from pyhopper.Core.Atoms import AtomicRectangle, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._helpers import array_result, checked_count, combined_vector, scaled_vector


class RectangularArray(Component):
    """Create a two-dimensional array using a rectangle's local cell spacing."""

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("cell", AtomicRectangle, Access.ITEM, default=AtomicRectangle()),
        InputParam("x_count", int, Access.ITEM, default=2),
        InputParam("y_count", int, Access.ITEM, default=2),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, cell=AtomicRectangle(), x_count=2, y_count=2):
        transforms = [
            AtomicTransform.translation(combined_vector(
                scaled_vector(cell.plane.x_axis, x * cell.x_size),
                scaled_vector(cell.plane.y_axis, y * cell.y_size),
            ))
            for y in range(checked_count(y_count))
            for x in range(checked_count(x_count))
        ]
        return array_result(geometry, transforms)
