"""Negative - Negate a numeric value."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Negative(Component):
    """Negate a numeric value.

    Accepts one number and returns its additive inverse.
    """

    inputs = [InputParam("value", float, Access.ITEM, default=0.0)]
    outputs = [OutputParam("result", float)]

    def generate(self, value=0.0):
        return -float(value)
