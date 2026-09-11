"""NurbsCurve - Construct a NURBS curve from control points."""

from pyhopper.Core.Atoms import (
    AtomicControlPointCurve,
    AtomicInterval,
    AtomicNurbsCurve,
    AtomicPoint,
)
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import nurbs_curve_domain, nurbs_curve_length
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve



def _periodic_curve(points: tuple[AtomicPoint, ...], degree: int) -> AtomicNurbsCurve:
    wrapped_points = points + points[:degree]
    point_count = len(points)
    knots = tuple(
        (index - degree) / point_count
        for index in range(len(wrapped_points) + degree + 1)
    )
    return AtomicNurbsCurve(
        control_points=wrapped_points,
        weights=tuple(1.0 for _ in wrapped_points),
        knots=knots,
        degree=degree,
    )


class NurbsCurve(Component):
    """Construct a NURBS curve from control points.

    Vertices are consumed as one branch-level list. Open curves are clamped
    through their first and last control points; periodic curves wrap the
    first ``degree`` points and remain smooth across their seam.
    """

    display_name = "Nurbs Curve"
    nickname = "Nurbs"
    gh_guid = "dde71aef-d6ed-40a6-af98-6b0673983c82"

    inputs = [
        InputParam("vertices", AtomicPoint, Access.LIST),
        InputParam("degree", int, Access.ITEM, default=3),
        InputParam("periodic", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("curve", AtomicNurbsCurve),
        OutputParam("length", float),
        OutputParam("domain", AtomicInterval),
    ]

    def generate(self, vertices=None, degree=3, periodic=False):
        points = tuple(vertices or ())
        if len(points) < 2:
            raise ValueError("NurbsCurve requires at least two control points")
        if not all(isinstance(point, AtomicPoint) for point in points):
            raise TypeError("NurbsCurve vertices must all be AtomicPoint values")

        curve_degree = max(1, min(int(degree), len(points) - 1))
        is_periodic = bool(periodic)
        curve = (
            _periodic_curve(points, curve_degree)
            if is_periodic
            else as_nurbs_curve(AtomicControlPointCurve(points, curve_degree))
        )
        domain_start, domain_end = nurbs_curve_domain(curve)
        return curve, nurbs_curve_length(curve), AtomicInterval(domain_start, domain_end)
