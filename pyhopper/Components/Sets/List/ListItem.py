"""ListItem - Select one item from a list branch by index."""

from __future__ import annotations

import builtins
from typing import Any

from pyhopper.Core.Branch import Branch
from pyhopper.Core.Component import Access, Component, ComponentResult, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path


def _coerce_bool(values: list[Any], default: bool = False) -> bool:
    if not values:
        return default
    return bool(values[0])


def _coerce_indices(values: list[Any]) -> list[int]:
    if not values:
        return [0]
    return [int(value) for value in values]


def _nearest_branch(tree: DataTree, target_path: Path) -> list[Any]:
    if target_path in tree.paths:
        return list(tree.branch(target_path))
    if not tree.paths:
        return []
    return list(tree.branch(tree.paths[-1]))


class ListItem(Component):
    """Select items from each input branch by index.

    Accepts one branch of list data, one or more integer indices, and an
    optional ``wrap`` flag. It returns one output item per incoming index while
    preserving branch structure. ``wrap`` controls whether out-of-range indices
    cycle around the branch length or return no item.
    """

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("index", int, Access.LIST, default=0),
        InputParam("wrap", bool, Access.LIST, default=False),
    ]
    outputs = [OutputParam("item")]

    def __new__(cls, *args: Any, **kwargs: Any) -> ComponentResult:
        instance = object.__new__(cls)
        input_trees = instance._coerce_inputs(*args, **kwargs)
        list_tree = input_trees["list"]
        index_tree = input_trees["index"]
        wrap_tree = input_trees["wrap"]

        principal = max(
            (list_tree, index_tree, wrap_tree),
            key=lambda tree: (tree.branch_count, max((path.depth for path in tree.paths), default=0)),
        )
        output_branches: dict[Path, list[Any]] = {}

        for path in sorted(principal.paths):
            result = instance.generate(
                list=_nearest_branch(list_tree, path),
                index=_nearest_branch(index_tree, path),
                wrap=_nearest_branch(wrap_tree, path),
            )
            output_branches[path] = list(result) if isinstance(result, (tuple, builtins.list)) else [result]

        output_tree = DataTree({path: Branch(path, items) for path, items in output_branches.items()})
        return ComponentResult(output_tree, {"item": output_tree})

    def generate(self, list=None, index=0, wrap=False):
        """Return the selected items from the incoming branch."""
        branch = list if isinstance(list, (tuple, builtins.list)) else [list]
        if not branch:
            return []

        wrap_enabled = _coerce_bool(wrap if isinstance(wrap, builtins.list) else [wrap])
        count = len(branch)
        indices = _coerce_indices(index if isinstance(index, builtins.list) else [index])
        result = []

        for raw_index in indices:
            resolved_index = raw_index % count if wrap_enabled else raw_index
            if 0 <= resolved_index < count:
                result.append(branch[resolved_index])

        return result
