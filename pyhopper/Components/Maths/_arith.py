"""Shared arithmetic over the value kinds Grasshopper's Maths components accept.

Numbers, text (concatenation), vectors and points can be added; means are defined
for numbers, vectors and points. Mixed kinds raise ``TypeError`` so a component
fails loudly instead of guessing.
"""

from __future__ import annotations

from typing import Any, Sequence

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Utils.Vectors import add as _vector_add

Spatial = (AtomicPoint, AtomicVector)


def is_number(value: Any) -> bool:
    """True for ints and floats, but not for bools."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def add(a: Any, b: Any, component: str = "Addition") -> Any:
    """``a + b`` for numbers, text, vectors and points (point + vector -> point)."""
    if is_number(a) and is_number(b):
        return float(a) + float(b)
    if isinstance(a, str) and isinstance(b, str):
        return a + b
    if isinstance(a, Spatial) and isinstance(b, Spatial):
        return _vector_add(a, b)
    raise TypeError(f"{component} cannot add {type(a).__name__} and {type(b).__name__}")


def mean(items: Sequence[Any], component: str = "Average") -> Any:
    """Arithmetic mean of numbers, vectors or points (any point makes the result a point)."""
    if not items:
        raise ValueError(f"{component} requires at least one item")
    count = len(items)
    if all(is_number(item) for item in items):
        return sum(float(item) for item in items) / count
    if all(isinstance(item, Spatial) for item in items):
        x = sum(item.x for item in items) / count
        y = sum(item.y for item in items) / count
        z = sum(item.z for item in items) / count
        result_type = AtomicPoint if any(isinstance(item, AtomicPoint) for item in items) else AtomicVector
        return result_type(x, y, z)
    raise TypeError(f"{component} needs a list of numbers, vectors or points")
