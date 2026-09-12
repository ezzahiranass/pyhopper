"""Boolean - Typed boolean parameter container."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Boolean(Component):
    """Contain strict boolean values."""

    inputs = [InputParam("boolean", bool, Access.ITEM)]
    outputs = [OutputParam("boolean", bool)]

    def generate(self, boolean=False):
        return boolean
