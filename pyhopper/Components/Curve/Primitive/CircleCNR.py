"""CircleCNR - Create a circle from center, normal, and radius."""

from pyhopper.Core.Atoms import AtomicCircle, AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _cross_product(a: AtomicVector, b: AtomicVector) -> AtomicVector:
    return AtomicVector(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    )


def _dot_product(a: AtomicVector, b: AtomicVector) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


def _orthonormal_x_axis(normal: AtomicVector) -> AtomicVector:
    reference = AtomicVector.unit_x()
    if abs(_dot_product(normal, reference)) > 0.99:
        reference = AtomicVector.unit_y()
    y_axis = _cross_product(normal, reference).unitize()
    return _cross_product(y_axis, normal).unitize()


class CircleCNR(Component):
    """Create an ``AtomicCircle`` from a center, normal, and radius.

    Accepts a center point, a normal vector, and a radius, then constructs
    the corresponding circle in a derived plane.
    """

    inputs = [
        InputParam("center", AtomicPoint, Access.ITEM),
        InputParam("normal", AtomicVector, Access.ITEM, default=None, optional=True),
        InputParam("radius", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("circle")]

    def generate(self, center=None, normal=None, radius=1.0):
        if normal is None:
            normal = AtomicVector.unit_z()
        normal_unit = normal.unitize()
        x_axis = _orthonormal_x_axis(normal_unit)
        plane = AtomicPlane(origin=center, normal=normal_unit, x_axis=x_axis)
        return AtomicCircle(plane=plane, radius=float(radius))
