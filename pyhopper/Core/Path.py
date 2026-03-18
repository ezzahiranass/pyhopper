"""
Path - Immutable address for a branch within a DataTree.

Mirrors Grasshopper's GH_Path: a tuple of non-negative integers
representing a hierarchical location like {0;2;1}.
"""

from __future__ import annotations


class Path(tuple):
    """Immutable branch address in a DataTree.

    >>> p = Path(0, 2, 1)
    >>> str(p)
    '{0;2;1}'
    >>> p.depth
    3
    """

    def __new__(cls, *indices: int) -> Path:
        if len(indices) == 1 and isinstance(indices[0], (list, tuple)):
            indices = tuple(indices[0])
        return super().__new__(cls, indices)

    # ── Class constructors ──────────────────────────────────────────

    @classmethod
    def root(cls) -> Path:
        """The default single-branch path {0}."""
        return cls(0)

    @classmethod
    def parse(cls, s: str) -> Path:
        """Parse a Grasshopper-style path string like '{0;2;1}'."""
        s = s.strip().strip("{}")
        if not s:
            return cls(0)
        return cls(*(int(x) for x in s.split(";")))

    @classmethod
    def from_json(cls, data: list[int]) -> Path:
        """Reconstruct from a JSON-serializable list."""
        return cls(*data)

    # ── Properties ──────────────────────────────────────────────────

    @property
    def depth(self) -> int:
        """Number of indices in this path."""
        return len(self)

    # ── Operations (all return new Path, never mutate) ──────────────

    def append(self, index: int) -> Path:
        """Return a new Path with *index* appended at the end."""
        return Path(*self, index)

    def prepend(self, index: int) -> Path:
        """Return a new Path with *index* prepended at the start."""
        return Path(index, *self)

    def trim(self, depth: int) -> Path:
        """Return a new Path truncated to the first *depth* elements."""
        return Path(*self[:depth])

    def common_prefix(self, other: Path) -> Path:
        """Return the longest shared prefix between this path and *other*."""
        shared = []
        for a, b in zip(self, other):
            if a != b:
                break
            shared.append(a)
        return Path(*shared) if shared else Path(0)

    # ── Serialization ───────────────────────────────────────────────

    def to_json(self) -> list[int]:
        """Serialize to a JSON-compatible list of ints."""
        return list(self)

    # ── Display ─────────────────────────────────────────────────────

    def __str__(self) -> str:
        return "{" + ";".join(str(i) for i in self) + "}"

    def __repr__(self) -> str:
        return f"Path({', '.join(str(i) for i in self)})"
