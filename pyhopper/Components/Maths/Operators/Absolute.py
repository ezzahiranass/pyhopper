"""Absolute - Return the absolute value of a number."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Absolute(Component):
    """Return the absolute value of a number.

    Accepts one number and returns its non-negative magnitude.
    """

    inputs = [InputParam("value", float, Access.ITEM, default=0.0)]
    outputs = [OutputParam("result", float)]

    def generate(self, value=0.0):
        return abs(float(value))
