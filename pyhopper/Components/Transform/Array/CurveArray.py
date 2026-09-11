"""CurveArray - Array geometry along a rail curve."""

from pyhopper.Core.Atoms import AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._helpers import array_result, curve_array_transforms


class CurveArray(Component):
    """Array geometry at equal rail-length intervals using stable perpendicular frames."""

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("curve", None, Access.ITEM),
        InputParam("count", int, Access.ITEM, default=10),
    ]
    outputs = [
        OutputParam("geometry", access=Access.LIST),
        OutputParam("transform", AtomicTransform, access=Access.LIST),
    ]

    def generate(self, geometry=None, curve=None, count=10):
        return array_result(geometry, curve_array_transforms(curve, count))
