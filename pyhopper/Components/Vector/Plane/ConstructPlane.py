"""ConstructPlane - Create a plane from origin, x-axis, and y-axis."""

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ConstructPlane(Component):
    """Create an ``AtomicPlane`` from origin, x-axis, and y-axis vectors.

    Mirrors Grasshopper's Construct Plane component: the plane is defined by
    an origin point and two in-plane axis vectors.
    """

    inputs = [
        InputParam("origin", AtomicPoint, Access.ITEM, default=AtomicPoint.origin()),
        InputParam("x_axis", AtomicVector, Access.ITEM, default=AtomicVector.unit_x()),
        InputParam("y_axis", AtomicVector, Access.ITEM, default=AtomicVector.unit_y()),
    ]
    outputs = [OutputParam("plane", AtomicPlane)]

    def generate(self, origin=None, x_axis=None, y_axis=None):
        if origin is None:
            origin = AtomicPoint.origin()

        if x_axis is None or x_axis.length == 0:
            x_axis = AtomicVector.unit_x()
        else:
            x_axis = x_axis.unitize()

        if y_axis is None or y_axis.length == 0:
            y_axis = AtomicVector.unit_y()
        else:
            y_axis = y_axis.unitize()

        normal = AtomicVector(
            x_axis.y * y_axis.z - x_axis.z * y_axis.y,
            x_axis.z * y_axis.x - x_axis.x * y_axis.z,
            x_axis.x * y_axis.y - x_axis.y * y_axis.x,
        ).unitize()

        if normal.length == 0:
            normal = AtomicVector.unit_z()
            x_axis = AtomicVector.unit_x()
        else:
            x_axis = AtomicVector(
                y_axis.y * normal.z - y_axis.z * normal.y,
                y_axis.z * normal.x - y_axis.x * normal.z,
                y_axis.x * normal.y - y_axis.y * normal.x,
            ).unitize()

        return AtomicPlane(origin=origin, normal=normal, x_axis=x_axis)
