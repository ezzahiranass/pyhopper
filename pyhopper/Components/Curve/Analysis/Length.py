"""Length - Measure the length of a curve."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Curves import curve_length


class Length(Component):
    """Measure the arc length of any supported curve atom."""

    inputs = [InputParam("curve", None, Access.ITEM)]
    outputs = [OutputParam("length", float)]

    def generate(self, curve=None):
        return curve_length(curve)
