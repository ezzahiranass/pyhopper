"""Text formatting shared by the Text components and the ``str`` coercion.

Grasshopper turns numbers into text with .NET's shortest round-trip
formatting: ``1.0`` becomes ``1``, ``2.5`` stays ``2.5``, ``1e-7`` becomes
``1E-07`` and ``0.1 + 0.2`` prints all of ``0.30000000000000004``. Python's
``repr`` already produces the shortest round-trip digits, so only the integral
and exponent spellings need adjusting.
"""

from __future__ import annotations

import math
from typing import Any

# .NET switches to exponent notation for magnitudes >= 1E+15; Python does so at 1e16.
_EXPONENT_THRESHOLD = 1e15


def format_number(value: float | int) -> str:
    """Format a number the way Grasshopper's text ports do."""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int):
        return str(value)
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "∞" if value > 0 else "-∞"
    if value == int(value) and abs(value) < _EXPONENT_THRESHOLD:
        return str(int(value))
    text = repr(value)
    if abs(value) >= _EXPONENT_THRESHOLD and "e" not in text:
        # 1E+15 <= |value| < 1E+16: Python still prints fixed notation, .NET does not;
        # move the decimal point without touching repr's shortest round-trip digits
        sign = "-" if text.startswith("-") else ""
        integer, _, fraction = text.lstrip("-").partition(".")
        digits = (integer + fraction).rstrip("0") or "0"
        mantissa = digits[0] + (f".{digits[1:]}" if len(digits) > 1 else "")
        text = f"{sign}{mantissa}e+{len(integer) - 1}"
    if "e" in text:
        mantissa, exponent = text.split("e")
        if mantissa.endswith(".0"):
            mantissa = mantissa[:-2]
        sign = exponent[0] if exponent[0] in "+-" else "+"
        magnitude = exponent.lstrip("+-").rjust(2, "0")
        return f"{mantissa}E{sign}{magnitude}"
    return text


def format_value(value: Any) -> str:
    """Text for any primitive item: text passes through, numbers and booleans are formatted."""
    if isinstance(value, str):
        return value
    if isinstance(value, (bool, int, float)):
        return format_number(value)
    return str(value)
