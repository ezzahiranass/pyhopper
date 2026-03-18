"""NumberSlider - Provide a numeric parameter with a slider-style frontend preset."""

from __future__ import annotations

from pyhopper.Core.Component import Component, OutputParam


class NumberSlider(Component):
    """Provide a numeric parameter as a zero-input component.

    This component follows the standard :class:`pyhopper.Core.Component.Component`
    contract: it declares no inputs, exposes one output named ``value``, and
    returns a single float from ``generate()``. Tree coercion, branch handling,
    path propagation, and result wrapping are all inherited unchanged from the
    base class.

    The optional ``frontend_preset`` metadata allows the web canvas to render
    this parameter as an interactive slider. That metadata is declarative only;
    it does not replace the normal component solve model.
    """

    DEFAULT_MIN = 0.0
    DEFAULT_MAX = 1.0
    DEFAULT_STEP = 0.01
    DEFAULT_DECIMALS = 2
    DEFAULT_VALUE = 0.5

    inputs = []
    outputs = [OutputParam("value", float)]
    frontend_preset = "number-slider"
    frontend_config = {
        "min": DEFAULT_MIN,
        "max": DEFAULT_MAX,
        "step": DEFAULT_STEP,
        "decimals": DEFAULT_DECIMALS,
        "value": DEFAULT_VALUE,
    }

    def generate(self) -> float:
        """Return the component's default numeric value."""
        return float(self.DEFAULT_VALUE)
