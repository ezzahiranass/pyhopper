"""Domain - Typed numeric-domain parameter container."""

from pyhopper.Core.Atoms import AtomicInterval
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Domain(Component):
    """Contain a DataTree of numeric intervals."""

    inputs = [InputParam("domain", AtomicInterval, Access.ITEM)]
    outputs = [OutputParam("domain", AtomicInterval)]

    def generate(self, domain=None):
        return domain
