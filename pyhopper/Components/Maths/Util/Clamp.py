"""Clamp - Restrict a number between two numeric extremes (Grasshopper "Clamp")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Clamp(Component):
    """Restrict a number between two numeric extremes.

    Inputs:
        value: Item to restrict between two numeric extremes (Grasshopper Value [item]).
        domain: Domain between two numberic extremes (Grasshopper Domain [item]).

    Outputs:
        clamped: Clamped value (Grasshopper Clamped).

    Notes:
        Grasshopper: Maths > Util > Clamp (Clamp).
        pyhopper decisions: numeric values only; a reversed domain is normalised first
        (Grasshopper 8 returns the domain start for every value when the domain is reversed).
    """

    display_name = "Clamp"
    nickname = "Clamp"
    gh_guid = "116df248-630e-4045-8c81-58693d1ff3a4"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
        InputParam("domain", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
    ]
    outputs = [
        OutputParam("clamped", float),
    ]

    def generate(self, value=0.0, domain=AtomicInterval(0.0, 1.0)):
        low, high = sorted((float(domain.start), float(domain.end)))
        return min(high, max(low, float(value)))
