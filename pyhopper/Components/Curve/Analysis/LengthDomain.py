"""LengthDomain - Measure the length of a curve subdomain (Grasshopper "Length Domain")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_domain_of, curve_length_at
from pyhopper.Core.TypeSystem import CURVE


class LengthDomain(Component):
    """Measure the length of a curve subdomain.

    Inputs:
        curve: Curve to measure (Grasshopper Curve [item]).
        domain: Subdomain of curve to measure (Grasshopper Domain [item]).

    Outputs:
        length: Curve length on sub domain (Grasshopper Length).

    Notes:
        Grasshopper: Curve > Analysis > Length Domain (LenD).
        pyhopper decisions: the arc length between the two domain ends (negative when the domain runs
        backwards), each end clamped to the curve — Grasshopper-verified. Parameters are the curve's
        native ones.
    """

    display_name = "Length Domain"
    nickname = "LenD"
    gh_guid = "188edd02-14a9-4828-a521-34995b0d1e4a"

    inputs = [
        InputParam("curve", CURVE, Access.ITEM),
        InputParam("domain", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
    ]
    outputs = [
        OutputParam("length", float),
    ]

    def generate(self, curve=None, domain=AtomicInterval(0.0, 1.0)):
        low, high = curve_domain_of(curve)
        clamp = lambda t: min(max(float(t), low), high)
        return curve_length_at(curve, clamp(domain.end)) - curve_length_at(curve, clamp(domain.start))
