"""FitCurve - Fit a curve along another curve (Grasshopper "Fit Curve")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicLine, AtomicPolyline
from pyhopper.Utils.CurveEditing import fit_nurbs_curve, polyline_as_bezier_spans
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
from pyhopper.Core.TypeSystem import CURVE


class FitCurve(Component):
    """Fit a curve along another curve.

    Inputs:
        curve: Curve to fit (Grasshopper Curve [item]).
        degree: Optional degree of curve (if omitted, input degree is used) (Grasshopper Degree [item]).
        tolerance: Tolerance for fitting (if omitted, document tolerance is used) (Grasshopper Tolerance [item]).

    Outputs:
        curve: Fitted curve (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Util > Fit Curve (Fit).
        pyhopper decisions: polylines become exact Bezier spans of the requested degree (default 3)
        with chord-length knots and lines a degree-2 span, both as Grasshopper does; NURBS are refitted
        by least squares (``Utils.CurveFitting.rebuild_curve``) with the fewest control points that
        keep the sampled deviation within the tolerance (default 0.001) — Rhino's own fitter is not
        replicated, so only the structure is comparable.
    """

    display_name = "Fit Curve"
    nickname = "Fit"
    gh_guid = "a3f9f19e-3e6c-4ac7-97c3-946de32c3e8e"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("degree", int, Access.ITEM, optional=True),
        InputParam("tolerance", float, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("curve", CURVE),
    ]

    def generate(self, curve=None, degree=None, tolerance=None):
        fit_tolerance = 0.001 if tolerance is None else float(tolerance)
        if isinstance(curve, AtomicLine):
            return polyline_as_bezier_spans([curve.start, curve.end], 2 if degree is None else max(1, int(degree)))
        if isinstance(curve, AtomicPolyline):
            return polyline_as_bezier_spans(list(curve.points), 3 if degree is None else max(1, int(degree)))
        nurbs = as_nurbs_curve(curve)
        target_degree = nurbs.degree if degree is None else max(1, int(degree))
        return fit_nurbs_curve(nurbs, target_degree, fit_tolerance)
