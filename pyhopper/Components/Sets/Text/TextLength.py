"""TextLength - Count the characters in text."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class TextLength(Component):
    """Return the number of Unicode characters in each matched text value."""

    inputs = [InputParam("text", str, Access.ITEM)]
    outputs = [OutputParam("length", int)]

    def generate(self, text=""):
        return len(text)
