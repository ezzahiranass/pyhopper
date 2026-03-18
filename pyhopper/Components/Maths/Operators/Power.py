"""Power - Raise a numeric value to an exponent."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Power(Component):
    """Raise a numeric value to an exponent.

    Accepts a base and an exponent and returns ``base ** exponent``.
    """

    inputs = [
        InputParam("base", float, Access.ITEM, default=1.0),
        InputParam("exponent", float, Access.ITEM, default=2.0),
    ]
    outputs = [OutputParam("result", float)]

    def generate(self, base=1.0, exponent=2.0):
        return float(base) ** float(exponent)
