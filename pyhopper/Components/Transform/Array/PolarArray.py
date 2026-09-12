"""PolarArray - Array geometry around a plane axis."""

import math

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._helpers import array_result, checked_count


class PolarArray(Component):
    """Create a polar array over a sweep angle around a plane's normal."""

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("count", int, Access.ITEM, default=6),
        InputParam("angle", float, Access.ITEM, default=2.0 * math.pi),
    ]
    outputs = [
        OutputParam("geometry", access=Access.LIST),
        OutputParam("transform", AtomicTransform, access=Access.LIST),
    ]

    def generate(self, geometry=None, plane=AtomicPlane.world_xy(), count=6, angle=2.0 * math.pi):
        item_count = checked_count(count)
        step = float(angle) / item_count
        transforms = [
            AtomicTransform.rotation(plane.origin, plane.normal, index * step)
            for index in range(item_count)
        ]
        return array_result(geometry, transforms)
