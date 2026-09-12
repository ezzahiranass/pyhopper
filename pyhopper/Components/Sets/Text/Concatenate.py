"""Concatenate - Concatenate two text fragments."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Concatenate(Component):
    """Concatenate two matched text fragments into one text value."""

    inputs = [
        InputParam("fragment_a", str, Access.ITEM),
        InputParam("fragment_b", str, Access.ITEM),
    ]
    outputs = [OutputParam("result", str)]

    def generate(self, fragment_a="", fragment_b=""):
        return fragment_a + fragment_b
