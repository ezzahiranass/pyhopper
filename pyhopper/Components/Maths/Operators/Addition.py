"""Addition - Add two numeric values."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Addition(Component):
    """Add two numeric values.

    Accepts two numbers and returns their sum as a single numeric output.
    """

    inputs = [
        InputParam("a", float, Access.ITEM, default=0.0),
        InputParam("b", float, Access.ITEM, default=0.0),
    ]
    outputs = [OutputParam("result", float)]

    def generate(self, a=0.0, b=0.0):
        return float(a) + float(b)
