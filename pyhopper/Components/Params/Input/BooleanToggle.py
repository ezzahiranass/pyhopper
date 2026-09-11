"""BooleanToggle - Provide an authored True/False source value."""

from pyhopper.Core.Component import Component, OutputParam


class BooleanToggle(Component):
    """Provide one boolean value as a zero-input interactive source."""

    DEFAULT_VALUE = False

    inputs = []
    outputs = [OutputParam("value", bool)]
    settings_schema = {"value": {"type": "bool", "default": DEFAULT_VALUE}}

    def generate(self) -> bool:
        return self.DEFAULT_VALUE
