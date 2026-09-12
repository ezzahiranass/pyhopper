"""MDSlider - Provide an authored two-dimensional vector."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Component, OutputParam


class MDSlider(Component):
    """Provide one XY parameter vector as a zero-input interactive source."""

    DEFAULT_X = 0.5
    DEFAULT_Y = 0.5

    inputs = []
    outputs = [OutputParam("vector", AtomicVector)]
    settings_schema = {
        "x": {"type": "float", "default": DEFAULT_X},
        "y": {"type": "float", "default": DEFAULT_Y},
        "x_min": {"type": "float", "default": 0.0},
        "x_max": {"type": "float", "default": 1.0},
        "y_min": {"type": "float", "default": 0.0},
        "y_max": {"type": "float", "default": 1.0},
        "decimals": {"type": "int", "default": 2},
    }

    def generate(self) -> AtomicVector:
        return AtomicVector(self.DEFAULT_X, self.DEFAULT_Y, 0.0)
