"""ScaleNU - Scale geometry non-uniformly in a plane basis."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform


class ScaleNU(Component):
    """Scale geometry independently along a plane's local X, Y, and Z axes."""

    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("scale_x", float, Access.ITEM, default=1.0),
        InputParam("scale_y", float, Access.ITEM, default=1.0),
        InputParam("scale_z", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("geometry"),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, plane=AtomicPlane.world_xy(), scale_x=1.0, scale_y=1.0, scale_z=1.0):
        xform = AtomicTransform.scale_non_uniform(plane, scale_x, scale_y, scale_z)
        return apply_transform(xform, geometry), xform
