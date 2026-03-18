"""Circle3Pt - Create a circle through three points."""

import math

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Atoms import AtomicCircle, AtomicPlane, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _cross_product(a: AtomicVector, b: AtomicVector) -> AtomicVector:
    return AtomicVector(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    )


def _dot_product(a: AtomicVector, b: AtomicVector) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


class Circle3Pt(Component):
    """Create an ``AtomicCircle`` through three non-collinear points.

    Returns the circle together with the derived plane and radius.
    """

    inputs = [
        InputParam("a", AtomicPoint, Access.ITEM),
        InputParam("b", AtomicPoint, Access.ITEM),
        InputParam("c", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("circle"),
        OutputParam("plane"),
        OutputParam("radius", float),
    ]

    def generate(self, a=None, b=None, c=None):
        ab = AtomicVector(b.x - a.x, b.y - a.y, b.z - a.z)
        ac = AtomicVector(c.x - a.x, c.y - a.y, c.z - a.z)
        normal = _cross_product(ab, ac)
        normal_unit = normal.unitize()

        if normal.length == 0:
            raise ValueError("Circle3Pt requires three non-collinear points.")

        ex = ab.unitize()
        ey = _cross_product(normal_unit, ex).unitize()

        bx = ab.length
        cx = _dot_product(ac, ex)
        cy = _dot_product(ac, ey)
        determinant = 2.0 * bx * cy

        if determinant == 0:
            raise ValueError("Circle3Pt requires three non-collinear points.")

        ux = bx / 2.0
        uy = ((cx * cx) + (cy * cy) - (bx * cx)) / (2.0 * cy)

        center = AtomicPoint(
            a.x + ex.x * ux + ey.x * uy,
            a.y + ex.y * ux + ey.y * uy,
            a.z + ex.z * ux + ey.z * uy,
        )
        radius = math.sqrt(
            (center.x - a.x) ** 2 +
            (center.y - a.y) ** 2 +
            (center.z - a.z) ** 2
        )
        plane = AtomicPlane(origin=center, normal=normal_unit, x_axis=ex)
        circle = AtomicCircle(plane=plane, radius=radius)
        return circle, plane, radius
