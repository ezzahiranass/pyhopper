"""TweenCurve - Tween between two curves."""

from pyhopper.Core.Atoms import (
    AtomicCircle,
    AtomicLine,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicVector,
)
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_point(a: AtomicPoint, b: AtomicPoint, t: float) -> AtomicPoint:
    return AtomicPoint(_lerp(a.x, b.x, t), _lerp(a.y, b.y, t), _lerp(a.z, b.z, t))


def _lerp_vector(a: AtomicVector, b: AtomicVector, t: float) -> AtomicVector:
    return AtomicVector(_lerp(a.x, b.x, t), _lerp(a.y, b.y, t), _lerp(a.z, b.z, t))


def _lerp_plane(a: AtomicPlane, b: AtomicPlane, t: float) -> AtomicPlane:
    return AtomicPlane(
        origin=_lerp_point(a.origin, b.origin, t),
        normal=_lerp_vector(a.normal, b.normal, t).unitize(),
        x_axis=_lerp_vector(a.x_axis, b.x_axis, t).unitize(),
    )


def _tween_line(a: AtomicLine, b: AtomicLine, t: float) -> AtomicLine:
    return AtomicLine(
        start=_lerp_point(a.start, b.start, t),
        end=_lerp_point(a.end, b.end, t),
    )


def _tween_circle(a: AtomicCircle, b: AtomicCircle, t: float) -> AtomicCircle:
    return AtomicCircle(
        plane=_lerp_plane(a.plane, b.plane, t),
        radius=_lerp(a.radius, b.radius, t),
    )


def _tween_polyline(a: AtomicPolyline, b: AtomicPolyline, t: float) -> AtomicPolyline:
    count = max(a.count, b.count)
    if count == 0:
        return AtomicPolyline()

    def _sample(poly: AtomicPolyline, i: int, total: int) -> AtomicPoint:
        """Sample a polyline at evenly spaced index, stretching shorter ones."""
        if poly.count == 0:
            return AtomicPoint.origin()
        frac = i / max(total - 1, 1)
        pos = frac * max(poly.count - 1, 0)
        lo = int(pos)
        hi = min(lo + 1, poly.count - 1)
        sub_t = pos - lo
        return _lerp_point(poly.points[lo], poly.points[hi], sub_t)

    points = tuple(
        _lerp_point(_sample(a, i, count), _sample(b, i, count), t)
        for i in range(count)
    )
    return AtomicPolyline(points=points)


def _tween_nurbs(
    a: AtomicNurbsCurve, b: AtomicNurbsCurve, t: float
) -> AtomicNurbsCurve:
    if a.degree != b.degree:
        raise ValueError(
            f"Cannot tween NURBS curves of different degrees ({a.degree} vs {b.degree})"
        )
    if len(a.control_points) != len(b.control_points):
        raise ValueError(
            "Cannot tween NURBS curves with different numbers of control points "
            f"({len(a.control_points)} vs {len(b.control_points)})"
        )
    return AtomicNurbsCurve(
        control_points=tuple(
            _lerp_point(pa, pb, t)
            for pa, pb in zip(a.control_points, b.control_points)
        ),
        weights=tuple(
            _lerp(wa, wb, t) for wa, wb in zip(a.weights, b.weights)
        ),
        knots=a.knots,
        degree=a.degree,
    )


class TweenCurve(Component):
    """Tween between two curves.

    Accepts two curves of the same type and a factor between 0.0 and 1.0.
    At factor 0.0 the result matches Curve A; at 1.0 it matches Curve B.
    Supports ``AtomicLine``, ``AtomicCircle``, ``AtomicPolyline``, and
    ``AtomicNurbsCurve``.
    """

    inputs = [
        InputParam("curve_a", None, Access.ITEM),
        InputParam("curve_b", None, Access.ITEM),
        InputParam("factor", float, Access.ITEM, default=0.5),
    ]
    outputs = [OutputParam("tween")]

    def generate(self, curve_a=None, curve_b=None, factor=0.5):
        t = float(factor)

        if isinstance(curve_a, AtomicLine) and isinstance(curve_b, AtomicLine):
            return _tween_line(curve_a, curve_b, t)

        if isinstance(curve_a, AtomicCircle) and isinstance(curve_b, AtomicCircle):
            return _tween_circle(curve_a, curve_b, t)

        if isinstance(curve_a, AtomicPolyline) and isinstance(curve_b, AtomicPolyline):
            return _tween_polyline(curve_a, curve_b, t)

        if isinstance(curve_a, AtomicNurbsCurve) and isinstance(
            curve_b, AtomicNurbsCurve
        ):
            return _tween_nurbs(curve_a, curve_b, t)

        raise TypeError(
            f"Cannot tween between {type(curve_a).__name__} and {type(curve_b).__name__}. "
            "Both curves must be the same supported type."
        )
