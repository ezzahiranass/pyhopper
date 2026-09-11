"""Text - Typed text parameter container."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Text(Component):
    """Contain strict text values."""

    inputs = [InputParam("text", str, Access.ITEM)]
    outputs = [OutputParam("text", str)]

    def generate(self, text=""):
        return text
