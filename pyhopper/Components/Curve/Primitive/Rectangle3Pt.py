"""Rectangle3Pt - Create a rectangle from three points (Grasshopper "Rectangle 3Pt")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicRectangle
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Vectors import cross, dot, is_zero, length, sub, translate, unit, vector_between


class Rectangle3Pt(Component):
    """Create a rectangle from three points.

    Inputs:
        point_a: First corner of rectangle (Grasshopper Point A [item]).
        point_b: Second corner of rectangle (Grasshopper Point B [item]).
        point_c: Point along rectangle edge opposite to AB (Grasshopper Point C [item]).

    Outputs:
        rectangle: Rectangle defined by A, B and C. (Grasshopper Rectangle).
        length: Length of rectangle curve (Grasshopper Length).

    Notes:
        Grasshopper: Curve > Primitive > Rectangle 3Pt (Rec 3Pt).
        pyhopper decisions: the edge A→B is the x side and C's distance from that edge the y side; the
        rectangle's plane sits at its centre with x along A→B and C on the positive y side (so a C
        "below" flips the normal), ``length`` is the perimeter — all Grasshopper-verified.
    """

    display_name = "Rectangle 3Pt"
    nickname = "Rec 3Pt"
    gh_guid = "9bc98a1d-2ecc-407e-948a-09a09ed3e69d"

    inputs = [
        InputParam("point_a", AtomicPoint, Access.ITEM),
        InputParam("point_b", AtomicPoint, Access.ITEM),
        InputParam("point_c", AtomicPoint, Access.ITEM),
    ]
    outputs = [
        OutputParam("rectangle", AtomicRectangle),
        OutputParam("length", float),
    ]

    def generate(self, point_a=None, point_b=None, point_c=None):
        x_direction = vector_between(point_a, point_b)
        width = length(x_direction)
        to_c = sub(point_c, point_a)
        normal = cross(x_direction, to_c)
        if width < 1e-12 or is_zero(normal):
            raise ValueError("Rectangle3Pt needs three points that are not collinear")
        y_direction = unit(cross(normal, x_direction))
        height = dot(to_c, y_direction)
        centre = translate(translate(point_a, x_direction, 0.5), y_direction, height / 2.0)
        return AtomicRectangle(AtomicPlane(centre, normal, x_direction), width, height), 2.0 * (width + height)
