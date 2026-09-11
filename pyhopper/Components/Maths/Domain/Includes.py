"""Includes - Test a numeric value to see if it is included in the domain (Grasshopper "Includes")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Includes(Component):
    """Test a numeric value to see if it is included in the domain.

    Inputs:
        value: Value to test for inclusion (Grasshopper Value [item]).
        domain: Domain to test with (Grasshopper Domain [item]).

    Outputs:
        includes: True if the value is included in the domain (Grasshopper Includes).
        deviation: Distance between the value and the nearest value inside the domain (Grasshopper Deviation).

    Notes:
        Grasshopper: Maths > Domain > Includes (Inc).
        pyhopper decisions: ``deviation`` is zero inside the domain, otherwise the distance to the nearest
        bound; reversed domains are normalised first.
    """

    display_name = "Includes"
    nickname = "Inc"
    gh_guid = "f217f873-92f1-47ae-ad71-ca3c5a45c3f8"

    inputs = [
        InputParam("value", float, Access.ITEM, default=0.0),
        InputParam("domain", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
    ]
    outputs = [
        OutputParam("includes", bool),
        OutputParam("deviation", float),
    ]

    def generate(self, value=0.0, domain=AtomicInterval(0.0, 1.0)):
        low, high = sorted((float(domain.start), float(domain.end)))
        x = float(value)
        if low <= x <= high:
            return True, 0.0
        return False, (low - x) if x < low else (x - high)
