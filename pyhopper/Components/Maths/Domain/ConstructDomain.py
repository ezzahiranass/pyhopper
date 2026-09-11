"""ConstructDomain - Create a numeric domain from two extremes."""

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ConstructDomain(Component):
    """Create an ``AtomicInterval`` from a start and end value."""

    inputs = [
        InputParam("start", float, Access.ITEM, default=0.0),
        InputParam("end", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("domain", AtomicInterval)]

    def generate(self, start=0.0, end=1.0):
        return AtomicInterval(float(start), float(end))
