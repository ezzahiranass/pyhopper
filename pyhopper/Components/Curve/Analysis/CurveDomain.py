"""CurveDomain - Measure and set the curve domain (Grasshopper "Curve Domain")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_domain_of, redomain_nurbs_curve
from pyhopper.Core.TypeSystem import CURVE


class CurveDomain(Component):
    """Measure and set the curve domain.

    Inputs:
        curve: Curve to measure/modify (Grasshopper Curve [item]).
        domain: Optional domain, if omitted the curve will not be modified. (Grasshopper Domain [item]).

    Outputs:
        curve: Curve with new domain. (Grasshopper Curve).
        domain: Domain of original curve. (Grasshopper Domain).

    Notes:
        Grasshopper: Curve > Analysis > Curve Domain (CrvDom).
        pyhopper decisions: ``domain`` reports the curve's native domain — [0, 1] for named curve atoms (what a
        reparameterised Grasshopper curve has; Grasshopper's own natives are arc length for arcs,
        length for lines and segment index for polylines) and the knot domain for NURBS. Supplying
        a domain converts the curve to NURBS and remaps its knots affinely.
    """

    display_name = "Curve Domain"
    nickname = "CrvDom"
    gh_guid = "ccfd6ba8-ecb1-44df-a47e-08126a653c51"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("domain", AtomicInterval, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("curve", CURVE),
        OutputParam("domain", AtomicInterval),
    ]

    def generate(self, curve=None, domain=None):
        start, end = curve_domain_of(curve)
        if domain is None:
            return curve, AtomicInterval(start, end)
        from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve
        return redomain_nurbs_curve(as_nurbs_curve(curve), (domain.start, domain.end)), AtomicInterval(start, end)
