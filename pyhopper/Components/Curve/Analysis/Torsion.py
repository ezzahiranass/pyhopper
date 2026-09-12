"""Torsion - Evaluate the torsion of a curve at a specified parameter (Grasshopper "Torsion")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Differential import curve_analysis, torsion
from pyhopper.Core.TypeSystem import CURVE


class Torsion(Component):
    """Evaluate the torsion of a curve at a specified parameter.

    Inputs:
        curve: Curve to evaluate (Grasshopper Curve [item]).
        parameter: Parameter on curve domain to evaluate (Grasshopper Parameter [item]).

    Outputs:
        point: Point on curve at {t} (Grasshopper Point).
        torsion: Curvature torsion at {t} (Grasshopper Torsion).

    Notes:
        Grasshopper: Curve > Analysis > Torsion (Torsion).
        pyhopper decisions: Grasshopper-verified — the Frenet torsion ``((r' × r'') · r''') / |r' × r''|²``,
        zero on straight stretches. ``parameter`` is the curve's native parameter (use the Reparameterize port operation for [0, 1]).
    """

    display_name = "Torsion"
    nickname = "Torsion"
    gh_guid = "dbe9fce4-b6b3-465f-9615-34833c4763bd"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("parameter", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("point", AtomicPoint),
        OutputParam("torsion", float),
    ]

    def generate(self, curve=None, parameter=0.0):
        analysis = curve_analysis(curve, float(parameter))
        return analysis.point, torsion(analysis)
