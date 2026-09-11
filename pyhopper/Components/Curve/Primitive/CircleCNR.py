"""CircleCNR - Create a circle from center, normal, and radius."""

from pyhopper.Core.Atoms import AtomicCircle, AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Vectors import cross, dot


def _orthonormal_x_axis(normal: AtomicVector) -> AtomicVector:
    reference = AtomicVector.unit_x()
    if abs(dot(normal, reference)) > 0.99:
        reference = AtomicVector.unit_y()
    y_axis = cross(normal, reference).unitize()
    return cross(y_axis, normal).unitize()


class CircleCNR(Component):
    """Create an ``AtomicCircle`` from a center, normal, and radius.

    Accepts a center point, a normal vector, and a radius, then constructs
    the corresponding circle in a derived plane.
    """

    inputs = [
        InputParam("center", AtomicPoint, Access.ITEM),
        InputParam("normal", AtomicVector, Access.ITEM, default=AtomicVector.unit_z()),
        InputParam("radius", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("circle")]

    def generate(self, center=None, normal=AtomicVector.unit_z(), radius=1.0):
        normal_unit = normal.unitize()
        x_axis = _orthonormal_x_axis(normal_unit)
        plane = AtomicPlane(origin=center, normal=normal_unit, x_axis=x_axis)
        return AtomicCircle(plane=plane, radius=float(radius))
