"""MDSlider - Provide an authored two-dimensional vector."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Component, OutputParam


class MDSlider(Component):
    """Provide one XY parameter vector as a zero-input interactive source."""

    DEFAULT_X = 0.5
    DEFAULT_Y = 0.5

    inputs = []
    outputs = [OutputParam("vector", AtomicVector)]
    # the pad's range and precision are settings; the handle position is authored
    settings_schema = {
        "x_min": {"type": "float", "default": 0.0, "label": "X minimum"},
        "x_max": {"type": "float", "default": 1.0, "label": "X maximum"},
        "y_min": {"type": "float", "default": 0.0, "label": "Y minimum"},
        "y_max": {"type": "float", "default": 1.0, "label": "Y maximum"},
        "decimals": {"type": "int", "default": 2, "min": 0, "max": 12, "label": "Decimals"},
    }
    authored_values = {
        "x": {"type": "float", "default": DEFAULT_X, "label": "X"},
        "y": {"type": "float", "default": DEFAULT_Y, "label": "Y"},
    }
    authored_emit = "vector"

    def generate(self) -> AtomicVector:
        return AtomicVector(self.DEFAULT_X, self.DEFAULT_Y, 0.0)
