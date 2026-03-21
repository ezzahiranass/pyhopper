"""Range - Create a range of numbers."""

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Range(Component):
    """Create a range of evenly spaced numbers within a domain.

    Divides the domain into ``steps`` equal parts and returns ``steps + 1``
    values — the start, all intermediate points, and the end of the domain.
    Mirrors the Grasshopper Sets > Sequence > Range component.
    """

    inputs = [
        InputParam("domain", AtomicInterval, Access.ITEM, default=AtomicInterval(0.0, 1.0)),
        InputParam("steps", int, Access.ITEM, default=10),
    ]
    outputs = [OutputParam("range")]

    def generate(self, domain=AtomicInterval(0.0, 1.0), steps=10):
        n = max(int(steps), 1)
        return [domain.start + (i / n) * (domain.end - domain.start) for i in range(n + 1)]
