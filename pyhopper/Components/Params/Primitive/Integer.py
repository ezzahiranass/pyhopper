"""Integer - Typed integer parameter container."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Integer(Component):
    """Contain integers, rounding finite numeric inputs to the nearest integer."""

    inputs = [InputParam("integer", int, Access.ITEM)]
    outputs = [OutputParam("integer", int)]

    def generate(self, integer=0):
        return integer
