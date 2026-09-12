"""Number - Typed number parameter container."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Number(Component):
    """Contain finite numbers normalized to floats."""

    inputs = [InputParam("number", float, Access.ITEM)]
    outputs = [OutputParam("number", float)]

    def generate(self, number=0.0):
        return number
