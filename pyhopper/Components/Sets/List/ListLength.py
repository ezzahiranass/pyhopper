"""ListLength - Measure the number of items in each list branch."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ListLength(Component):
    """Return the number of items in each incoming DataTree branch."""

    inputs = [InputParam("list", None, Access.LIST)]
    outputs = [OutputParam("length", int)]

    def generate(self, list=None):
        """Return the length of the incoming branch."""
        return len(list or [])
