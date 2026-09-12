"""SubCurve - Construct a curve from the sub-domain of a base curve (Grasshopper "Sub Curve")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.CurveOps import sub_curve
from pyhopper.Core.TypeSystem import CURVE


class SubCurve(Component):
    """Construct a curve from the sub-domain of a base curve.

    Inputs:
        base_curve: Base curve (Grasshopper Base curve [item]).
        domain: Sub-domain to extract (Grasshopper Domain [item]).

    Outputs:
        curve: Resulting sub curve (Grasshopper Curve).

    Notes:
        Grasshopper: Curve > Spline > Sub Curve (SubCrv).
        pyhopper decisions: Grasshopper-verified — the domain is sorted and clipped to the curve; the
        piece keeps the input's type and parameterisation (a NURBS sub-curve keeps its knot
        sub-domain). Grasshopper has no default domain; pyhopper's [0, 1] is the whole of a native
        curve. Polycurve segments keep their parameter spans the way Rhino assigns them (pieces of the input keep their parameter lengths, new segments get their natural span).
    """

    display_name = "Sub Curve"
    nickname = "SubCrv"
    gh_guid = "429cbba9-55ee-4e84-98ea-876c44db879a"

    inputs = [
        InputParam("base_curve", CURVE, Access.ITEM),
        InputParam("domain", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
    ]
    outputs = [
        OutputParam("curve", CURVE),
    ]

    def generate(self, base_curve=None, domain=AtomicInterval(0.0, 1.0)):
        return sub_curve(base_curve, float(domain.start), float(domain.end))
