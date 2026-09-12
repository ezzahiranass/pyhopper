"""CurveFrame - Get the curvature frame of a curve at a specified parameter (Grasshopper "Curve Frame")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Differential import curve_analysis, frenet_frame
from pyhopper.Core.TypeSystem import CURVE


class CurveFrame(Component):
    """Get the curvature frame of a curve at a specified parameter.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).
        parameter: Parameter on curve domain to evaluate (Grasshopper Parameter [item]).

    Outputs:
        frame: Curve frame at {t} (Grasshopper Frame).

    Notes:
        Grasshopper: Curve > Analysis > Curve Frame (Frame).
        pyhopper decisions: Grasshopper-verified — Rhino's curvature frame: x along the tangent, y
        towards the centre of curvature and z along the binormal; where the curvature vanishes y is
        openNURBS' perpendicular of the tangent (a line along X gets the world XY plane). ``parameter`` is the curve's native parameter (use the Reparameterize port operation for [0, 1]).
    """

    display_name = "Curve Frame"
    nickname = "Frame"
    gh_guid = "6b2a5853-07aa-4329-ba84-0a5d46b51dbd"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameter", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("frame", AtomicPlane),
    ]

    def generate(self, curve=None, parameter=0.0):
        return frenet_frame(curve_analysis(curve, float(parameter)))
