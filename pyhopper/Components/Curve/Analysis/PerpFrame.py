"""PerpFrame - Solve the perpendicular (zero-twisting) frame at a specified curve parameter (Grasshopper "Perp Frame")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_domain_of
from pyhopper.Utils.Frames import curve_perpendicular_frames
from pyhopper.Core.TypeSystem import CURVE


class PerpFrame(Component):
    """Solve the perpendicular (zero-twisting) frame at a specified curve parameter.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).
        parameter: Parameter on curve domain to evaluate (Grasshopper Parameter [item]).

    Outputs:
        frame: Perpendicular curve frame at {t} (Grasshopper Frame).

    Notes:
        Grasshopper: Curve > Analysis > Perp Frame (PFrame).
        pyhopper decisions: Rhino's ``PerpendicularFrameAt`` — the rotation-minimising frame swept from
        the curve start (whose x axis is the curvature direction there, else world Z then X) to the
        parameter; Grasshopper-verified on a twisting NURBS curve. Parameters are the curve's native
        ones.
    """

    display_name = "Perp Frame"
    nickname = "PFrame"
    gh_guid = "69f3e5ee-4770-44b3-8851-ae10ae555398"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameter", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("frame", AtomicPlane),
    ]

    def generate(self, curve=None, parameter=0.0):
        start, _ = curve_domain_of(curve)
        return curve_perpendicular_frames(curve, [start, float(parameter)])[-1]
