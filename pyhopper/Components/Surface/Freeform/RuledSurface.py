"""RuledSurface - Create a surface between two compatible curves."""

from __future__ import annotations

from dataclasses import dataclass

from pyhopper.Core.Atoms import AtomicNurbsCurve, AtomicSurface, _open_uniform_bspline_data
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


@dataclass(frozen=True)
class _CurveProfile:
    poles: tuple
    weights: tuple[float, ...]
    knots: tuple[float, ...]
    mults: tuple[int, ...]
    degree: int


def _collapse_repeated_knots(knots: tuple[float, ...]) -> tuple[tuple[float, ...], tuple[int, ...]]:
    if not knots:
        return (), ()

    unique_knots = [knots[0]]
    multiplicities = [1]

    for knot in knots[1:]:
        if knot == unique_knots[-1]:
            multiplicities[-1] += 1
        else:
            unique_knots.append(knot)
            multiplicities.append(1)

    return tuple(unique_knots), tuple(multiplicities)


def _nurbs_profile(curve: AtomicNurbsCurve) -> _CurveProfile:
    if len(curve.control_points) < 2:
        raise ValueError("RuledSurface requires NURBS curves with at least two control points")

    degree = max(1, min(int(curve.degree), len(curve.control_points) - 1))
    weights = curve.weights if len(curve.weights) == len(curve.control_points) else tuple(
        1.0 for _ in curve.control_points
    )

    if not curve.knots:
        knots, mults, degree = _open_uniform_bspline_data(len(curve.control_points), degree)
    else:
        raw_knots = tuple(float(knot) for knot in curve.knots)
        expected_full_count = len(curve.control_points) + degree + 1
        expected_unique_count = len(curve.control_points) - degree + 1

        if len(raw_knots) == expected_full_count:
            knots, mults = _collapse_repeated_knots(raw_knots)
        elif len(raw_knots) == expected_unique_count:
            knots = raw_knots
            mults = tuple(
                degree + 1 if index in (0, len(knots) - 1) else 1
                for index in range(len(knots))
            )
        else:
            raise ValueError(
                "RuledSurface could not interpret the NURBS knot vector; expected either "
                "a full knot vector or a unique-knot sequence matching the control point count."
            )

    return _CurveProfile(
        poles=curve.control_points,
        weights=weights,
        knots=knots,
        mults=mults,
        degree=degree,
    )

class RuledSurface(Component):
    """Create a ruled surface between two compatible curves.

    Accepts two curves per matched input item and returns one ``AtomicSurface``
    per pair while the inherited component pipeline preserves surrounding
    ``DataTree`` branch structure. Supported input curve types are
    ``AtomicLine``, ``AtomicPolyline``, ``AtomicCircle``, ``AtomicArc``, and
    ``AtomicNurbsCurve``.
    """

    inputs = [
        InputParam("curve_a", None, Access.ITEM),
        InputParam("curve_b", None, Access.ITEM),
    ]
    outputs = [OutputParam("surface", AtomicSurface)]

    def generate(self, curve_a=None, curve_b=None):
        """Return a ruled surface spanning the two input curves."""
        profile_a = _nurbs_profile(as_nurbs_curve(curve_a))
        profile_b = _nurbs_profile(as_nurbs_curve(curve_b))

        if profile_a.degree != profile_b.degree:
            raise ValueError(
                f"RuledSurface requires matching curve degrees ({profile_a.degree} vs {profile_b.degree})"
            )
        if len(profile_a.poles) != len(profile_b.poles):
            raise ValueError(
                "RuledSurface requires curves with matching control point counts "
                f"({len(profile_a.poles)} vs {len(profile_b.poles)})"
            )
        if profile_a.knots != profile_b.knots or profile_a.mults != profile_b.mults:
            raise ValueError(
                "RuledSurface requires curves with matching knot structure"
            )

        return AtomicSurface(
            poles=(profile_a.poles, profile_b.poles),
            weights=(profile_a.weights, profile_b.weights),
            u_knots=profile_a.knots,
            v_knots=(0.0, 1.0),
            u_mults=profile_a.mults,
            v_mults=(2, 2),
            u_degree=profile_a.degree,
            v_degree=1,
        )
