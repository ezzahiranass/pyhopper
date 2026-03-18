"""
DataTree - Hierarchical data structure mirroring Grasshopper's DataTree<T>.

A DataTree is an ordered collection of Branches, each addressed by a Path.
It supports tree operations (graft, flatten, simplify, flip), data matching
between multiple trees (longest list, shortest list, cross reference),
and JSON serialization.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from enum import Enum
from itertools import product
from typing import Any, Iterator

from .Branch import Branch
from .Path import Path


class MatchRule(Enum):
    LONGEST_LIST = "longest_list"
    SHORTEST_LIST = "shortest_list"
    CROSS_REFERENCE = "cross_reference"


class DataTree:
    """Hierarchical data container mirroring Grasshopper's DataTree."""

    __slots__ = ("_branches",)

    def __init__(self, branches: dict[Path, Branch] | None = None) -> None:
        self._branches: OrderedDict[Path, Branch] = OrderedDict()
        if branches:
            for path in sorted(branches.keys()):
                b = branches[path]
                if isinstance(b, Branch):
                    self._branches[path] = b
                else:
                    self._branches[path] = Branch(path, b)

    # ── Constructors ────────────────────────────────────────────────

    @classmethod
    def from_item(cls, value: Any) -> DataTree:
        """Create a tree with a single item at {0}."""
        path = Path.root()
        return cls({path: Branch(path, [value])})

    @classmethod
    def from_list(cls, items: list | tuple) -> DataTree:
        """Create a tree with one branch {0} containing all items."""
        path = Path.root()
        return cls({path: Branch(path, items)})

    @classmethod
    def from_branches(cls, data: dict[Path, list]) -> DataTree:
        """Create a tree from an explicit {Path: list} mapping."""
        branches = {}
        for path, items in data.items():
            branches[path] = Branch(path, items)
        return cls(branches)

    @classmethod
    def coerce(cls, value: Any) -> DataTree:
        """Normalize any value into a DataTree.

        - DataTree -> passthrough
        - list/tuple -> single branch {0} with all items
        - scalar/Atom -> single item at {0}
        """
        if isinstance(value, DataTree):
            return value
        if isinstance(value, (list, tuple)):
            return cls.from_list(value)
        return cls.from_item(value)

    # ── Accessors ───────────────────────────────────────────────────

    @property
    def branch_count(self) -> int:
        return len(self._branches)

    @property
    def paths(self) -> list[Path]:
        return list(self._branches.keys())

    def branch(self, path: Path) -> Branch:
        return self._branches[path]

    def branches(self) -> Iterator[tuple[Path, Branch]]:
        """Yield (path, branch) pairs."""
        yield from self._branches.items()

    def items(self) -> Iterator[tuple[Path, int, Any]]:
        """Yield (path, index, item) for every item in every branch."""
        for path, branch in self._branches.items():
            for i, item in enumerate(branch):
                yield path, i, item

    def all_items(self) -> list[Any]:
        """Flat list of all items, ignoring path structure."""
        result = []
        for branch in self._branches.values():
            result.extend(branch)
        return result

    def __iter__(self) -> Iterator[Any]:
        """Iterate over all items (flat), making DataTree iterable."""
        for branch in self._branches.values():
            yield from branch

    def __len__(self) -> int:
        """Total item count across all branches."""
        return sum(len(b) for b in self._branches.values())

    def __bool__(self) -> bool:
        return len(self._branches) > 0

    def __contains__(self, item: Any) -> bool:
        return any(item in b for b in self._branches.values())

    # ── Tree Operations (all return new DataTree) ───────────────────

    def flatten(self) -> DataTree:
        """Collapse all branches into a single branch at {0}."""
        all_items = self.all_items()
        path = Path.root()
        return DataTree({path: Branch(path, all_items)})

    def graft(self) -> DataTree:
        """Each item becomes its own branch.

        Item at {a;b}[i] moves to {a;b;i}[0].
        """
        branches = {}
        for path, branch in self._branches.items():
            for i, item in enumerate(branch):
                new_path = path.append(i)
                branches[new_path] = Branch(new_path, [item])
        return DataTree(branches)

    def simplify(self) -> DataTree:
        """Remove the longest common path prefix from all branches."""
        if len(self._branches) <= 1:
            path = Path.root()
            items = self.all_items()
            return DataTree({path: Branch(path, items)})

        all_paths = list(self._branches.keys())
        prefix = all_paths[0]
        for p in all_paths[1:]:
            prefix = prefix.common_prefix(p)

        trim_depth = prefix.depth
        if trim_depth == 0:
            return DataTree(dict(self._branches))

        branches = {}
        for path, branch in self._branches.items():
            new_path = Path(*path[trim_depth:]) if len(path) > trim_depth else Path.root()
            branches[new_path] = Branch(new_path, list(branch))
        return DataTree(branches)

    def flip_matrix(self) -> DataTree:
        """Transpose: swap branch-index and item-index dimensions.

        A tree with N branches of M items each becomes M branches of N items.
        """
        all_paths = list(self._branches.keys())
        if not all_paths:
            return DataTree()

        max_items = max(len(b) for b in self._branches.values())
        branches = {}
        for i in range(max_items):
            new_path = Path(i)
            items = []
            for path in all_paths:
                branch = self._branches[path]
                if i < len(branch):
                    items.append(branch[i])
                elif branch:
                    items.append(branch[-1])  # repeat last
            branches[new_path] = Branch(new_path, items)
        return DataTree(branches)

    def trim(self, depth: int) -> DataTree:
        """Truncate all paths to *depth*, merging branches that collide."""
        branches: dict[Path, list] = {}
        for path, branch in self._branches.items():
            new_path = path.trim(depth) if path.depth > depth else path
            if new_path in branches:
                branches[new_path].extend(branch)
            else:
                branches[new_path] = list(branch)
        return DataTree.from_branches(branches)

    @classmethod
    def entwine(cls, *trees: DataTree) -> DataTree:
        """Merge multiple trees, prepending each tree's branches with a unique index."""
        branches = {}
        for i, tree in enumerate(trees):
            for path, branch in tree._branches.items():
                new_path = path.prepend(i)
                branches[new_path] = Branch(new_path, list(branch))
        return cls(branches)

    @classmethod
    def merge(cls, *trees: DataTree) -> DataTree:
        """Combine branches from multiple trees, merging items on path collision."""
        branches: dict[Path, list] = {}
        for tree in trees:
            for path, branch in tree._branches.items():
                if path in branches:
                    branches[path].extend(branch)
                else:
                    branches[path] = list(branch)
        return cls.from_branches(branches)

    # ── Data Matching ───────────────────────────────────────────────

    @classmethod
    def match(
        cls,
        trees: list[DataTree],
        rule: MatchRule = MatchRule.LONGEST_LIST,
    ) -> Iterator[tuple[Path, list[list[Any]]]]:
        """Match branches and items across multiple input trees.

        Yields (output_path, matched_items_per_input) tuples where
        matched_items_per_input[i] is the list of items from trees[i]
        for this iteration step.

        Branch matching uses longest-list (repeat last branch).
        Item matching within branches uses the specified rule.
        """
        if not trees:
            return

        # Determine the principal tree: the one with the most branches,
        # breaking ties by deepest max path depth. Its paths drive iteration.
        principal = max(
            trees,
            key=lambda t: (t.branch_count, max((p.depth for p in t.paths), default=0)),
        )
        sorted_paths = sorted(principal.paths)

        # For each path in the principal tree, find matching branches in others
        for path in sorted_paths:
            branches_per_input = []
            for tree in trees:
                branch = _find_nearest_branch(tree, path)
                branches_per_input.append(branch)

            # Match items within matched branches
            yield from _match_items(path, branches_per_input, rule)

    # ── Serialization ───────────────────────────────────────────────

    def to_json(self) -> dict:
        return {
            "type": "DataTree",
            "branches": [b.to_json() for b in self._branches.values()],
        }

    @classmethod
    def from_json(cls, data: dict) -> DataTree:
        branches = {}
        for b_data in data["branches"]:
            branch = Branch.from_json(b_data)
            branches[branch.path] = branch
        return cls(branches)

    def to_json_string(self, indent: int = 2) -> str:
        return json.dumps(self.to_json(), indent=indent)

    # ── Display ─────────────────────────────────────────────────────

    def __repr__(self) -> str:
        lines = [f"DataTree ({self.branch_count} branches, {len(self)} items):"]
        for path, branch in self._branches.items():
            items_repr = ", ".join(repr(item) for item in branch[:5])
            if len(branch) > 5:
                items_repr += f", ... ({len(branch)} total)"
            lines.append(f"  {path}: [{items_repr}]")
        return "\n".join(lines)


# ── Internal helpers ────────────────────────────────────────────────


def _find_nearest_branch(tree: DataTree, target_path: Path) -> list:
    """Find the branch in tree matching target_path, or the last branch."""
    if target_path in tree._branches:
        return list(tree._branches[target_path])

    # Repeat-last: find the branch with the nearest path
    tree_paths = tree.paths
    if not tree_paths:
        return []
    return list(tree._branches[tree_paths[-1]])


def _match_items(
    path: Path,
    branches: list[list],
    rule: MatchRule,
) -> Iterator[tuple[Path, list[list[Any]]]]:
    """Match items across branches using the specified rule."""
    if rule == MatchRule.LONGEST_LIST:
        yield path, _longest_list_match(branches)
    elif rule == MatchRule.SHORTEST_LIST:
        yield path, _shortest_list_match(branches)
    elif rule == MatchRule.CROSS_REFERENCE:
        yield from _cross_reference_match(path, branches)


def _longest_list_match(branches: list[list]) -> list[list]:
    """Zip items, repeating the last item of shorter lists."""
    if not branches:
        return []

    max_len = max((len(b) for b in branches), default=0)
    if max_len == 0:
        return [[] for _ in branches]

    result = [[] for _ in branches]
    for i in range(max_len):
        for j, branch in enumerate(branches):
            if i < len(branch):
                result[j].append(branch[i])
            elif branch:
                result[j].append(branch[-1])  # repeat last
    return result


def _shortest_list_match(branches: list[list]) -> list[list]:
    """Zip items, stopping at the shortest list."""
    if not branches:
        return []

    min_len = min((len(b) for b in branches), default=0)
    result = [[] for _ in branches]
    for i in range(min_len):
        for j, branch in enumerate(branches):
            result[j].append(branch[i])
    return result


def _cross_reference_match(
    path: Path,
    branches: list[list],
) -> Iterator[tuple[Path, list[list[Any]]]]:
    """Cartesian product of all items across branches."""
    if not branches or any(len(b) == 0 for b in branches):
        return

    indices = [range(len(b)) for b in branches]
    for combo in product(*indices):
        sub_path = path.append(combo[0]) if len(combo) > 0 else path
        items = [[branches[j][idx]] for j, idx in enumerate(combo)]
        yield sub_path, items
