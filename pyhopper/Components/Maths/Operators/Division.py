"""Division - Divide one numeric value by another."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Division(Component):
    """Divide one numeric value by another.

    Accepts two numbers and returns ``a / b`` as a single numeric output.
    """

    inputs = [
        InputParam("a", float, Access.ITEM, default=1.0),
        InputParam("b", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("result", float)]

    def generate(self, a=1.0, b=1.0):
        return float(a) / float(b)
