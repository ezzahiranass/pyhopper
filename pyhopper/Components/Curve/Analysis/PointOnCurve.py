"""PointOnCurve - Evaluate a point at normalized length along a curve."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import CURVE
from pyhopper.Utils.Curves import point_at_normalized_curve_length
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


class PointOnCurve(Component):
    """Evaluate one point on a curve using normalized arc length.

    Accepts any supported curve atom and a normalized ``parameter`` value where
    ``0.0`` is the start of the curve and ``1.0`` is the end. The inherited
    solve pipeline matches curve and parameter items while preserving
    ``DataTree`` paths.
    """

    DEFAULT_PARAMETER = 0.5

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameter", float, Access.ITEM, default=DEFAULT_PARAMETER),
    ]
    outputs = [OutputParam("point", AtomicPoint)]
    # the node's slider authors ``parameter``; unwired, it is passed as a literal
    authored_values = {
        "parameter": {"type": "float", "default": DEFAULT_PARAMETER, "min": 0.0, "max": 1.0, "label": "Parameter"},
    }

    def generate(self, curve=None, parameter=DEFAULT_PARAMETER):
        """Return the point at the requested normalized curve length."""
        return point_at_normalized_curve_length(as_nurbs_curve(curve), float(parameter))
