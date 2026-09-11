"""RuledSurface - Create a surface between two compatible curves."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicNurbsCurve, AtomicSurface
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Nurbs import curve_profile
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


class RuledSurface(Component):
    """Create a ruled surface between two compatible curves.

    Accepts two curves per matched input item and returns one ``AtomicSurface``
    per pair while the inherited component pipeline preserves surrounding
    ``DataTree`` branch structure. Supported input curve types are
    ``AtomicLine``, ``AtomicPolyline``, ``AtomicCircle``, ``AtomicArc``, and
    ``AtomicNurbsCurve``.
    """

    inputs = [
        InputParam("curve_a", CURVE, Access.ITEM),
        InputParam("curve_b", CURVE, Access.ITEM),
    ]
    outputs = [OutputParam("surface", AtomicSurface)]

    def generate(self, curve_a=None, curve_b=None):
        """Return a ruled surface spanning the two input curves."""
        profile_a = curve_profile(as_nurbs_curve(curve_a), "RuledSurface")
        profile_b = curve_profile(as_nurbs_curve(curve_b), "RuledSurface")

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
