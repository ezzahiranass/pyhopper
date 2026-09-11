"""DivideLength - Divide a curve into segments with a preset length (Grasshopper "Divide Length")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import divide_curve_by_length
from pyhopper.Core.TypeSystem import CURVE


class DivideLength(Component):
    """Divide a curve into segments with a preset length.

    Inputs:
        curve: Curve to divide (Grasshopper Curve [item]).
        length: Length of segments (Grasshopper Length [item]).

    Outputs:
        points: Division points (Grasshopper Points).
        tangents: Tangent vectors at division points (Grasshopper Tangents).
        parameters: Parameter values at division points (Grasshopper Parameters).

    Notes:
        Grasshopper: Curve > Division > Divide Length (DivLength).
        pyhopper decisions: points every ``length`` from the start; the end is included only when the length divides
        the curve exactly and the seam of a closed curve is not repeated; a length of zero (or less)
        raises ``ValueError`` where Grasshopper aborts with an error message. Parameters follow the
        curve's own parameterisation (see Evaluate Curve).
    """

    display_name = "Divide Length"
    nickname = "DivLength"
    gh_guid = "fdc466a9-d3b8-4056-852a-09dba0f74aca"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("length", float, Access.ITEM),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.LIST),
        OutputParam("tangents", AtomicVector, access=Access.LIST),
        OutputParam("parameters", float, access=Access.LIST),
    ]

    def generate(self, curve=None, length=None):
        return divide_curve_by_length(curve, length)
