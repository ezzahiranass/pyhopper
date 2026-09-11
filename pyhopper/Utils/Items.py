"""Item identity for set-style components (Create Set, Member Index, Item Index).

Grasshopper compares items by *type and value*: ``1``, ``1.0``, ``True`` and
``"1"`` are four different set members, while two points with the same
coordinates are one (verified against Grasshopper 8). ``item_key`` gives every
pyhopper item a hashable key with exactly those semantics.
"""

from __future__ import annotations

from typing import Any, Hashable


def item_key(value: Any) -> Hashable:
    """Type-sensitive equality key: same key <=> Grasshopper treats the items as equal."""
    kind = type(value).__name__
    try:
        hash(value)
    except TypeError:
        return (kind, repr(value))
    return (kind, value)


def index_of(items: list[Any], member: Any) -> int:
    """First index of ``member`` in ``items`` by :func:`item_key`, or ``-1``."""
    key = item_key(member)
    for index, item in enumerate(items):
        if item_key(item) == key:
            return index
    return -1


def indices_of(items: list[Any], member: Any) -> list[int]:
    """Every index of ``member`` in ``items`` by :func:`item_key`."""
    key = item_key(member)
    return [index for index, item in enumerate(items) if item_key(item) == key]
