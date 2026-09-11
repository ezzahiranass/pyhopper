"""
DataTree - Hierarchical data structure mirroring Grasshopper's DataTree<T>.

A DataTree is an ordered collection of Branches, each addressed by a Path.
It supports tree operations (graft, flatten, simplify, flip), data matching
between multiple trees (longest list, shortest list, cross reference),
and JSON serialization.
"""

from __future__ import annotations

import json
import math
from collections import OrderedDict
from enum import Enum
from itertools import product
from typing import Any, Iterator

from .Branch import Branch
from .Path import Path


def _is_invalid(item: Any) -> bool:
    """Grasshopper's notion of an invalid item, for pyhopper data: a non-finite number."""
    return isinstance(item, float) and not math.isfinite(item)


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
        - scalar/Atom/Path -> single item at {0} (a Path is a tuple, but it is one item)
        """
        if isinstance(value, DataTree):
            return value
        if isinstance(value, Path):
            return cls.from_item(value)
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
    #
    # These follow Grasshopper's data-tree components exactly (checked with the
    # headless oracle in rhino-test/oracle): Flatten, Graft, Simplify, Trim,
    # Flip Matrix, Entwine, Merge, Prune and Clean.

    def flatten(self, path: Path | None = None) -> DataTree:
        """Collapse every branch into one branch at ``path`` (default ``{0}``)."""
        target = Path.root() if path is None else Path(*path)
        return DataTree({target: Branch(target, self.all_items())})

    def graft(self) -> DataTree:
        """Each item becomes its own branch: ``{a;b}[i]`` moves to ``{a;b;i}[0]``.

        An empty branch survives as the empty sub-branch ``{a;b;0}`` (Grasshopper).
        """
        branches = {}
        for path, branch in self._branches.items():
            if not len(branch):
                new_path = path.append(0)
                branches[new_path] = Branch(new_path, [])
            for i, item in enumerate(branch):
                new_path = path.append(i)
                branches[new_path] = Branch(new_path, [item])
        return DataTree(branches)

    def simplify(self, front: bool = False) -> DataTree:
        """Remove the path indices that every branch shares (Grasshopper Simplify).

        Positions are compared up to the shortest path; with ``front`` only the
        leading run of shared positions is removed. When removing every shared
        position would leave the shortest path empty, its first index is kept
        (``{2;1}`` + ``{2;1;0}`` -> ``{2}`` + ``{2;0}``). A tree with a single
        branch is returned unchanged, exactly like Grasshopper.
        """
        paths = list(self._branches.keys())
        if len(paths) < 2:
            return DataTree(dict(self._branches))
        shortest = min(len(path) for path in paths)
        shared = [position for position in range(shortest) if len({path[position] for path in paths}) == 1]
        if front:
            leading = []
            for position in range(shortest):
                if position in shared:
                    leading.append(position)
                else:
                    break
            shared = leading
        if len(shared) == shortest and shared:
            shared = shared[1:]  # never empty the shortest path: keep its first index
        removed = set(shared)
        if not removed:
            return DataTree(dict(self._branches))
        branches = {}
        for path, branch in self._branches.items():
            new_path = Path(*(index for position, index in enumerate(path) if position not in removed))
            branches[new_path] = Branch(new_path, list(branch))
        return DataTree(branches)

    def reverse(self) -> DataTree:
        """Reverse the order of items in each branch."""
        branches = {}
        for path, branch in self._branches.items():
            branches[path] = Branch(path, list(reversed(branch)))
        return DataTree(branches)

    def flip_matrix(self) -> DataTree:
        """Swap rows and columns of a matrix-like tree (Grasshopper Flip Matrix).

        All paths must have the same length and may differ at a single index
        position (the *locus*); item ``i`` of every branch lands in the branch
        whose locus index is ``i``. Shorter branches are padded with ``None``
        (Grasshopper nulls). Raises ``ValueError`` for uneven or multi-locus paths.
        """
        paths = list(self._branches.keys())
        if not paths:
            return DataTree()
        length = len(paths[0])
        if any(len(path) != length for path in paths):
            raise ValueError("Flip Matrix needs paths of the same length")
        loci = [position for position in range(length) if len({path[position] for path in paths}) > 1]
        if len(loci) > 1:
            raise ValueError("Flip Matrix paths may only differ at a single index position")
        locus = loci[0] if loci else length - 1
        count = max(len(branch) for branch in self._branches.values())
        template = list(paths[0])
        branches = {}
        for i in range(count):
            template[locus] = i
            new_path = Path(*template)
            branches[new_path] = Branch(new_path, [branch[i] if i < len(branch) else None for branch in self._branches.values()])
        return DataTree(branches)

    def trim(self, depth: int) -> DataTree:
        """Remove the last ``depth`` indices of every path, merging colliding branches.

        Grasshopper's Trim Tree: ``{0;0;1}`` + ``{0;0;2}`` -> ``{0;0}`` at depth 1.
        Branches whose path is not longer than ``depth`` are omitted (Grasshopper
        drops them with a warning); a negative depth raises ``ValueError``.
        """
        if depth < 0:
            raise ValueError("Trim Tree depth has to be a positive integer")
        if depth == 0:
            return DataTree(dict(self._branches))
        branches: dict[Path, list] = {}
        for path, branch in self._branches.items():
            if len(path) <= depth:
                continue
            new_path = Path(*path[: len(path) - depth])
            branches.setdefault(new_path, []).extend(branch)
        return DataTree.from_branches(branches)

    def prune(self, minimum: int = 0, maximum: int = 0) -> DataTree:
        """Drop branches with fewer than ``minimum`` or more than ``maximum`` items.

        ``maximum = 0`` means no upper limit (Grasshopper Prune Tree).
        """
        branches = {}
        for path, branch in self._branches.items():
            count = len(branch)
            if count < minimum or (maximum > 0 and count > maximum):
                continue
            branches[path] = Branch(path, list(branch))
        return DataTree(branches)

    def clean(self, remove_nulls: bool = True, remove_invalid: bool = True, remove_empty: bool = False) -> DataTree:
        """Remove ``None`` items, invalid items and/or empty branches (Grasshopper Clean Tree).

        pyhopper atoms are always valid; "invalid" items are non-finite numbers.
        """
        branches = {}
        for path, branch in self._branches.items():
            items = list(branch)
            if remove_nulls:
                items = [item for item in items if item is not None]
            if remove_invalid:
                items = [item for item in items if not _is_invalid(item)]
            if remove_empty and not items:
                continue
            branches[path] = Branch(path, items)
        return DataTree(branches)

    @classmethod
    def entwine(cls, *trees: DataTree) -> DataTree:
        """Flatten each tree into its own branch ``{0;i}`` (Grasshopper Entwine)."""
        branches = {}
        for i, tree in enumerate(trees):
            new_path = Path(0, i)
            branches[new_path] = Branch(new_path, tree.all_items())
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
    def principal(cls, trees: list[DataTree]) -> DataTree:
        """The tree whose paths drive iteration: most branches, then deepest path.

        Ties keep the first tree, so declaration order matters.
        """
        if not trees:
            raise ValueError("principal() needs at least one tree")
        return max(
            trees,
            key=lambda t: (t.branch_count, max((p.depth for p in t.paths), default=0)),
        )

    def nearest_branch(self, target_path: Path) -> list:
        """Items at *target_path*, or of the last branch when the path is missing (repeat-last)."""
        return _find_nearest_branch(self, target_path)

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
        principal = cls.principal(trees)
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
    if max_len == 0 or any(len(b) == 0 for b in branches):
        # An empty branch has nothing to repeat: no item pairs exist.
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
