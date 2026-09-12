"""NumberSlider - Provide a numeric parameter with configurable settings."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Component, OutputParam


ROUNDING_MODES = frozenset({"real", "integer", "even", "odd"})


def _finite_number(value, fallback: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return fallback
    numeric = float(value)
    return numeric if math.isfinite(numeric) else fallback


def _round_half_away_from_zero(value: float) -> int:
    magnitude = math.floor(abs(value) + 0.5)
    return magnitude if value >= 0.0 else -magnitude


def _nearest_parity(value: float, parity: int) -> int:
    rounded = _round_half_away_from_zero(value)
    if rounded % 2 == parity:
        return rounded
    candidates = (rounded - 1, rounded + 1)
    return min(candidates, key=lambda candidate: (abs(candidate - value), abs(candidate)))


def normalize_number_slider_settings(settings: dict | None = None) -> dict[str, float | int | str]:
    """Return validated NumberSlider settings with defaults applied."""
    raw = settings or {}
    min_value = _finite_number(raw.get("min"), NumberSlider.DEFAULT_MIN)
    max_value = _finite_number(raw.get("max"), NumberSlider.DEFAULT_MAX)
    if max_value < min_value:
        min_value, max_value = max_value, min_value

    decimals = raw.get("decimals", NumberSlider.DEFAULT_DECIMALS)
    if isinstance(decimals, bool) or not isinstance(decimals, (int, float)) or not math.isfinite(float(decimals)):
        decimals = NumberSlider.DEFAULT_DECIMALS
    decimals = max(0, min(int(decimals), 12))

    rounding = str(raw.get("rounding", NumberSlider.DEFAULT_ROUNDING)).lower()
    if rounding not in ROUNDING_MODES:
        rounding = NumberSlider.DEFAULT_ROUNDING

    value = _finite_number(raw.get("value"), NumberSlider.DEFAULT_VALUE)
    return {
        "value": value,
        "min": min_value,
        "max": max_value,
        "decimals": decimals,
        "rounding": rounding,
    }


def apply_number_slider_settings(settings: dict | None = None) -> float:
    """Clamp and round a slider value according to its settings."""
    normalized = normalize_number_slider_settings(settings)
    min_value = float(normalized["min"])
    max_value = float(normalized["max"])
    value = min(max(float(normalized["value"]), min_value), max_value)

    rounding = normalized["rounding"]
    if rounding == "integer":
        value = float(_round_half_away_from_zero(value))
    elif rounding == "even":
        value = float(_nearest_parity(value, 0))
    elif rounding == "odd":
        value = float(_nearest_parity(value, 1))
    else:
        value = round(value, int(normalized["decimals"]))

    return min(max(value, min_value), max_value)


class NumberSlider(Component):
    """Provide a numeric parameter as a zero-input component.

    This component follows the standard :class:`pyhopper.Core.Component.Component`
    contract: it declares no inputs, exposes one output named ``value``, and
    returns a single float from ``generate()``. Tree coercion, branch handling,
    path propagation, and result wrapping are all inherited unchanged from the
    base class.

    Optional ``_settings`` passed at call time define the authored slider
    range, precision, rounding, and value without adding graph input ports or
    bypassing the inherited solve model.
    """

    DEFAULT_MIN = 0.0
    DEFAULT_MAX = 1.0
    DEFAULT_DECIMALS = 2
    DEFAULT_VALUE = 0.5
    DEFAULT_ROUNDING = "real"

    inputs = []
    outputs = [OutputParam("value", float)]
    settings_schema = {
        "value": {"type": "float", "default": DEFAULT_VALUE},
        "min": {"type": "float", "default": DEFAULT_MIN},
        "max": {"type": "float", "default": DEFAULT_MAX},
        "decimals": {"type": "int", "default": DEFAULT_DECIMALS, "min": 0, "max": 12},
        "rounding": {
            "type": "choice",
            "default": DEFAULT_ROUNDING,
            "choices": ["real", "integer", "even", "odd"],
        },
    }

    def generate(self) -> float:
        """Return the authored numeric value after backend validation."""
        return apply_number_slider_settings(self.settings)
