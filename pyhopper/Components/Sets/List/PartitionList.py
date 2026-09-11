"""PartitionList - Partition each list branch into fixed-size chunks."""

from __future__ import annotations

import builtins
from typing import Any

from pyhopper.Core.Branch import Branch
from pyhopper.Core.Component import Access, Component, ComponentResult, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path


def _nearest_branch(tree: DataTree, target_path: Path) -> list[Any]:
    if target_path in tree.paths:
        return list(tree.branch(target_path))
    if not tree.paths:
        return []
    return list(tree.branch(tree.paths[-1]))


def _first_int(value: Any, default: int) -> int:
    values = value if isinstance(value, builtins.list) else [value]
    return int(values[0]) if values else default


class PartitionList(Component):
    """Partition every incoming branch into fixed-size sub-branches.

    Each chunk is written to ``{original path; chunk index}``. Partition sizes
    below one are clamped to one.
    """

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("size", int, Access.LIST, default=2),
    ]
    outputs = [OutputParam("chunks")]

    def __new__(cls, *args: Any, **kwargs: Any) -> ComponentResult:
        instance = object.__new__(cls)
        input_trees = instance._coerce_inputs(*args, **kwargs)
        list_tree = input_trees["list"]
        size_tree = input_trees["size"]
        output_branches: dict[Path, list[Any]] = {}

        for path in list_tree.paths:
            chunks = instance.generate(
                list=list(list_tree.branch(path)),
                size=_nearest_branch(size_tree, path),
            )
            if not chunks:
                output_branches[path.append(0)] = []
                continue
            for index, chunk in enumerate(chunks):
                output_branches[path.append(index)] = chunk

        output_tree = DataTree(
            {path: Branch(path, items) for path, items in output_branches.items()}
        )
        return ComponentResult(output_tree, {"chunks": output_tree})

    def generate(self, list=None, size=2):
        """Return fixed-size chunks from the incoming branch."""
        branch = list if isinstance(list, builtins.list) else [list]
        partition_size = max(1, _first_int(size, 2))
        return [
            branch[index : index + partition_size]
            for index in range(0, len(branch), partition_size)
        ]
