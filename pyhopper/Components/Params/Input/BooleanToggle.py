"""BooleanToggle - Provide an authored True/False source value."""

from pyhopper.Core.Component import Component, OutputParam


class BooleanToggle(Component):
    """Provide one boolean value as a zero-input interactive source."""

    DEFAULT_VALUE = False

    inputs = []
    outputs = [OutputParam("value", bool)]
    authored_values = {"value": {"type": "bool", "default": DEFAULT_VALUE, "label": "Value"}}
    authored_emit = "literal"

    def generate(self) -> bool:
        return self.DEFAULT_VALUE
