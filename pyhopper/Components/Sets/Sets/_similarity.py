"""Similarity score for Find Similar Member (lower is more similar)."""

from __future__ import annotations

from typing import Any

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Utils.Text import levenshtein
from pyhopper.Utils.TextFormat import value_text
from pyhopper.Utils.Vectors import distance


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def similarity_score(data: Any, member: Any) -> float:
    """Absolute difference for two numbers, distance for two points, otherwise the edit distance of
    the Grasshopper text forms (which is what Grasshopper falls back to)."""
    if _is_number(data) and _is_number(member):
        return abs(float(data) - float(member))
    if isinstance(data, AtomicPoint) and isinstance(member, AtomicPoint):
        return distance(data, member)
    return float(levenshtein(value_text(data), value_text(member)))
