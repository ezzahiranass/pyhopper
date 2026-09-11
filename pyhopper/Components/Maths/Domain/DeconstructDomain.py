"""DeconstructDomain - Split a numeric domain into its extremes."""

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DeconstructDomain(Component):
    """Return the start and end values of an ``AtomicInterval``."""

    inputs = [
        InputParam("domain", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
    ]
    outputs = [
        OutputParam("start", float),
        OutputParam("end", float),
    ]

    def generate(self, domain=AtomicInterval(0.0, 1.0)):
        return float(domain.start), float(domain.end)
