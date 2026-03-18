"""Factorial - Compute the factorial of an integer."""

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Factorial(Component):
    """Compute the factorial of an integer.

    Accepts one integer and returns ``n!`` as a single integer output.
    """

    inputs = [InputParam("n", int, Access.ITEM, default=0)]
    outputs = [OutputParam("result", int)]

    def generate(self, n=0):
        return math.factorial(int(n))
