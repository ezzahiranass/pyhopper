"""BoxArray - Array geometry in a three-dimensional box cell grid."""

from pyhopper.Core.Atoms import AtomicBox, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._helpers import array_result, checked_count, combined_vector, scaled_vector


class BoxArray(Component):
    """Create a three-dimensional array using a box's local cell spacing."""

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("cell", AtomicBox, Access.ITEM, default=AtomicBox()),
        InputParam("x_count", int, Access.ITEM, default=2),
        InputParam("y_count", int, Access.ITEM, default=2),
        InputParam("z_count", int, Access.ITEM, default=2),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, cell=AtomicBox(), x_count=2, y_count=2, z_count=2):
        transforms = [
            AtomicTransform.translation(combined_vector(
                scaled_vector(cell.plane.x_axis, x * cell.x_size),
                scaled_vector(cell.plane.y_axis, y * cell.y_size),
                scaled_vector(cell.plane.normal, z * cell.z_size),
            ))
            for z in range(checked_count(z_count))
            for y in range(checked_count(y_count))
            for x in range(checked_count(x_count))
        ]
        return array_result(geometry, transforms)
