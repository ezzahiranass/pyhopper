"""Panel - Display and pass through arbitrary DataTree content."""

from __future__ import annotations

import math
import re

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


_INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")
_FLOAT_PATTERN = re.compile(
    r"^[+-]?(?:(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)$"
)


def parse_panel_text(text: str):
    """Parse a single-line authored Panel value into a scalar when unambiguous.

    Multiline content and non-literals remain text. Boolean matching is
    case-insensitive, while numeric parsing accepts signed integers, decimals,
    and scientific notation.
    """
    if "\n" in text or "\r" in text:
        return text

    candidate = text.strip()
    normalized = candidate.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    if _INTEGER_PATTERN.fullmatch(candidate):
        return int(candidate)
    if _FLOAT_PATTERN.fullmatch(candidate):
        value = float(candidate)
        return value if math.isfinite(value) else text
    return text


def parse_panel_lines(text: str) -> list:
    """Parse each authored line as one item in a single DataTree branch."""
    return [parse_panel_text(line) for line in re.split(r"\r\n|\r|\n", text)]


class Panel(Component):
    """Display a tree's contents while passing its data through unchanged.

    Grasshopper's Panel is primarily a debugging and inspection parameter. In
    pyhopper it keeps the standard component solve model: one input named
    ``data``, one output named ``data``, and a branch-wise pass-through
    ``generate()`` implementation.
    """

    inputs = [InputParam("data", None, Access.LIST, default=[])]
    outputs = [OutputParam("data")]

    def generate(self, data=None):
        """Return the matched branch contents unchanged."""
        return [] if data is None else data
