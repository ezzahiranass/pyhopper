"""Series - Generate a list of evenly spaced numbers."""

from pyhopper.Core.Component import Component, InputParam, OutputParam, Access


class Series(Component):
    """Generate a list of evenly spaced numbers.

    The output is a single-branch tree of ``count`` floats starting at
    ``start`` and increasing by ``step``.
    """

    inputs = [
        InputParam("start", float, Access.ITEM, default=0.0),
        InputParam("step", float, Access.ITEM, default=1.0),
        InputParam("count", int, Access.ITEM, default=10),
    ]
    outputs = [OutputParam("series")]

    def generate(self, start=0.0, step=1.0, count=10):
        start_value = float(start)
        step_value = float(step)
        count_value = int(count)
        return [start_value + step_value * index for index in range(count_value)]
