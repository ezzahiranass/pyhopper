"""
Branch - A list of items at a specific Path within a DataTree.

Subclasses list so all normal list operations work, but carries
an immutable path attribute for its location in the tree.
"""

from __future__ import annotations

from typing import Any, Iterable

from .Path import Path


def _item_to_json(item: Any) -> Any:
    """Serialize a single item (Atom or scalar) to JSON."""
    if hasattr(item, "to_json"):
        return item.to_json()
    return item


def _item_from_json(data: Any) -> Any:
    """Deserialize a single item from JSON."""
    # Import here to avoid circular dependency
    from .Atoms import ATOM_REGISTRY

    if isinstance(data, dict) and "type" in data:
        atom_cls = ATOM_REGISTRY.get(data["type"])
        if atom_cls is not None:
            return atom_cls.from_json(data)
    return data


class Branch(list):
    """A list of items located at a specific Path in a DataTree.

    >>> from pyhopper.Core.Path import Path
    >>> b = Branch(Path(0, 1), [10, 20, 30])
    >>> b.path
    Path(0, 1)
    >>> len(b)
    3
    """

    def __init__(self, path: Path, items: Iterable = ()) -> None:
        super().__init__(items)
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    # ── Serialization ───────────────────────────────────────────────

    def to_json(self) -> dict:
        return {
            "path": self._path.to_json(),
            "items": [_item_to_json(item) for item in self],
        }

    @classmethod
    def from_json(cls, data: dict) -> Branch:
        path = Path.from_json(data["path"])
        items = [_item_from_json(item) for item in data["items"]]
        return cls(path, items)

    # ── Display ─────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Branch({self._path!r}, {list.__repr__(self)})"
