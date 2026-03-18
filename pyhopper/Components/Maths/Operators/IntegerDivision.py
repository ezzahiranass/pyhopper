"""IntegerDivision - Divide two integers using floor division."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class IntegerDivision(Component):
    """Divide two integers using floor division.

    Accepts two integers and returns ``a // b`` as a single integer output.
    """

    inputs = [
        InputParam("a", int, Access.ITEM, default=1),
        InputParam("b", int, Access.ITEM, default=1),
    ]
    outputs = [OutputParam("result", int)]

    def generate(self, a=1, b=1):
        return int(a) // int(b)
