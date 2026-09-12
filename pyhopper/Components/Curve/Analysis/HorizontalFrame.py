"""HorizontalFrame - Get a horizontally aligned frame along a curve at a specified parameter (Grasshopper "Horizontal Frame")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_point_at, curve_tangent_at
from pyhopper.Utils.Frames import horizontal_frame
from pyhopper.Core.TypeSystem import CURVE


class HorizontalFrame(Component):
    """Get a horizontally aligned frame along a curve at a specified parameter.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).
        parameter: Parameter on curve domain to evaluate (Grasshopper Parameter [item]).

    Outputs:
        frame: Horizontal curve frame at {t} (Grasshopper Frame).

    Notes:
        Grasshopper: Curve > Analysis > Horizontal Frame (HFrame).
        pyhopper decisions: normal world Z, x axis the tangent projected onto the horizontal plane; a
        vertical tangent falls back to world X (Grasshopper-verified). Parameters are the curve's
        native ones.
    """

    display_name = "Horizontal Frame"
    nickname = "HFrame"
    gh_guid = "c048ad76-ffcd-43b1-a007-4dd1b2373326"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameter", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("frame", AtomicPlane),
    ]

    def generate(self, curve=None, parameter=0.0):
        return horizontal_frame(curve_point_at(curve, float(parameter)), curve_tangent_at(curve, float(parameter)))
