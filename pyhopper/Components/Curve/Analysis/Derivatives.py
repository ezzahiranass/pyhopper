"""Derivatives - Evaluate the derivatives of a curve at a specified parameter (Grasshopper "Derivatives")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Differential import curve_analysis
from pyhopper.Core.TypeSystem import CURVE


class Derivatives(Component):
    """Evaluate the derivatives of a curve at a specified parameter.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).
        parameter: Parameter on curve domain to evaluate (Grasshopper Parameter [item]).

    Outputs:
        point: Point on curve at {t} (Grasshopper Point).
        first_derivative: First curve derivative at t (Velocity) (Grasshopper First derivative).

    Notes:
        Grasshopper: Curve > Analysis > Derivatives (CDiv).
        pyhopper decisions: the first derivative in the curve's own parameterisation (Grasshopper
        exposes more derivatives through its zoomable interface; only the first is declared here).
        ``parameter`` is the curve's native parameter (use the Reparameterize port operation for [0, 1]).
    """

    display_name = "Derivatives"
    nickname = "CDiv"
    gh_guid = "ab14760f-87a6-462e-b481-4a2c26a9a0d7"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameter", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("first_derivative", AtomicVector),
    ]

    def generate(self, curve=None, parameter=0.0):
        analysis = curve_analysis(curve, float(parameter))
        return analysis.point, analysis.first
