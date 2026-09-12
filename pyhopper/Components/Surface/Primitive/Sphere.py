"""Sphere - Create an exact rational sphere surface."""

import math

from pyhopper.Core.Atoms import (
    AtomicArc,
    AtomicCircle,
    AtomicInterval,
    AtomicPlane,
    AtomicPoint,
    AtomicSurface,
    AtomicVector,
    _collapse_repeated_knots,
)
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Planes import coerce_base_plane
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Utils.Vectors import dot


def _offset(point: AtomicPoint, origin: AtomicPoint) -> AtomicVector:
    return AtomicVector(point.x - origin.x, point.y - origin.y, point.z - origin.z)


def _point_from_axes(
    origin: AtomicPoint,
    x_axis: AtomicVector,
    y_axis: AtomicVector,
    normal: AtomicVector,
    x: float,
    y: float,
    z: float,
) -> AtomicPoint:
    return AtomicPoint(
        origin.x + x_axis.x * x + y_axis.x * y + normal.x * z,
        origin.y + x_axis.y * x + y_axis.y * y + normal.y * z,
        origin.z + x_axis.z * x + y_axis.z * y + normal.z * z,
    )


class Sphere(Component):
    """Create an exact rational ``AtomicSurface`` sphere from a base plane."""

    inputs = [
        InputParam("base", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("radius", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("sphere", AtomicSurface)]

    def generate(self, base=AtomicPlane.world_xy(), radius=1.0):
        sphere_radius = abs(float(radius))
        if sphere_radius <= 0.0:
            raise ValueError("Sphere radius must be greater than zero")

        base = coerce_base_plane(base)
        normal = base.normal.unitize()
        x_axis = base.x_axis.unitize()
        if normal.length == 0.0 or x_axis.length == 0.0 or abs(dot(normal, x_axis)) > 1e-9:
            raise ValueError("Sphere base must have non-zero perpendicular normal and x axes")
        plane = AtomicPlane(base.origin, normal, x_axis)
        y_axis = plane.y_axis.unitize()

        circle = as_nurbs_curve(AtomicCircle(plane=plane, radius=1.0))
        meridian_plane = AtomicPlane(
            origin=plane.origin,
            normal=AtomicVector(-y_axis.x, -y_axis.y, -y_axis.z),
            x_axis=x_axis,
        )
        meridian = as_nurbs_curve(AtomicArc(
            plane=meridian_plane,
            radius=sphere_radius,
            angle=AtomicInterval(-math.pi / 2.0, math.pi / 2.0),
        ))

        poles = []
        weights = []
        for meridian_point, meridian_weight in zip(meridian.control_points, meridian.weights):
            meridian_offset = _offset(meridian_point, plane.origin)
            radial = dot(meridian_offset, x_axis)
            height = dot(meridian_offset, normal)
            pole_row = []
            weight_row = []
            for circle_point, circle_weight in zip(circle.control_points, circle.weights):
                circle_offset = _offset(circle_point, plane.origin)
                circle_x = dot(circle_offset, x_axis)
                circle_y = dot(circle_offset, y_axis)
                pole_row.append(_point_from_axes(
                    plane.origin,
                    x_axis,
                    y_axis,
                    normal,
                    radial * circle_x,
                    radial * circle_y,
                    height,
                ))
                weight_row.append(circle_weight * meridian_weight)
            poles.append(tuple(pole_row))
            weights.append(tuple(weight_row))

        u_knots, u_mults = _collapse_repeated_knots(circle.knots)
        v_knots, v_mults = _collapse_repeated_knots(meridian.knots)
        return AtomicSurface(
            poles=tuple(poles),
            weights=tuple(weights),
            u_knots=u_knots,
            v_knots=v_knots,
            u_mults=u_mults,
            v_mults=v_mults,
            u_degree=circle.degree,
            v_degree=meridian.degree,
        )
