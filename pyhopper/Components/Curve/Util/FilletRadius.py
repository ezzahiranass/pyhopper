"""FilletRadius - Fillet the sharp corners of a curve (Grasshopper "Fillet")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import fillet_radius
from pyhopper.Core.TypeSystem import CURVE


class FilletRadius(Component):
    """Fillet the sharp corners of a curve.

    Inputs:
        curve: Curve to fillet (Grasshopper Curve [item]).
        radius: Radius of fillet (Grasshopper Radius [item]).

    Outputs:
        curve: Curve with filleted corners (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Util > Fillet (Fillet).
        pyhopper decisions: Grasshopper-verified — every polyline corner is rounded with an arc of
        the radius; where the tangent length ``r·tan(θ/2)`` does not fit, the arc shrinks to what the
        edges allow (half of a shared edge), as Grasshopper does. A zero radius returns the curve, a
        negative one raises ``ValueError``, a curve without corners comes back wrapped in a polycurve.
        Grasshopper has no default radius.
    """

    display_name = "Fillet"
    nickname = "Fillet"
    gh_guid = "2f407944-81c3-4062-a485-276454ec4b8c"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("radius", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("curve", CURVE),
    ]

    def generate(self, curve=None, radius=0.0):
        return fillet_radius(curve, float(radius))
