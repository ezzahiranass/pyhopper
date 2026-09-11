"""List helpers shared by the Sets components (patterns, indices, padding).

The rules mirror Grasshopper (verified against Grasshopper 8 with the headless
oracle): patterns repeat to the length of the list they drive, ``wrap`` makes
an index modulo the list length, and positions past the end are padded with
``None`` where Grasshopper pads with nulls.
"""

from __future__ import annotations

from typing import Any, Sequence


def cycle(pattern: Sequence[Any], length: int) -> list[Any]:
    """Repeat ``pattern`` until it has ``length`` items (an empty pattern stays empty)."""
    if not pattern or length <= 0:
        return []
    return [pattern[index % len(pattern)] for index in range(length)]


def resolve_index(index: int, length: int, wrap: bool, component: str) -> int:
    """Index into a list of ``length`` items; ``wrap`` takes it modulo the length.

    Without ``wrap`` an index outside ``[0, length)`` raises ``IndexError`` with
    the component's name, the way Grasshopper reports "Index too high".
    """
    position = int(index)
    if wrap:
        if length <= 0:
            raise IndexError(f"{component} cannot wrap an index around an empty list")
        return position % length
    if not 0 <= position < length:
        raise IndexError(f"{component} index {position} is out of range for {length} items")
    return position


def pad_to(items: list[Any], length: int) -> list[Any]:
    """Extend ``items`` in place with ``None`` until it has at least ``length`` items."""
    if length > len(items):
        items.extend([None] * (length - len(items)))
    return items
