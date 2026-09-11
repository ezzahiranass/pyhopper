"""CullIndex - Remove indexed elements from a list."""

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


class CullIndex(Component):
    """Remove all indexed elements from each list branch.

    When ``wrap`` is true, indices wrap into the branch range. Otherwise,
    out-of-range and negative indices are ignored.
    """

    inputs = [
        InputParam("list", None, Access.LIST),
        InputParam("indices", int, Access.LIST, default=0),
        InputParam("wrap", bool, Access.LIST, default=False),
    ]
    outputs = [OutputParam("list")]

    def __new__(cls, *args: Any, **kwargs: Any) -> ComponentResult:
        instance = object.__new__(cls)
        input_trees = instance._coerce_inputs(*args, **kwargs)
        list_tree = input_trees["list"]
        indices_tree = input_trees["indices"]
        wrap_tree = input_trees["wrap"]
        output_branches = {}

        for path in list_tree.paths:
            output_branches[path] = instance.generate(
                list=list(list_tree.branch(path)),
                indices=_nearest_branch(indices_tree, path),
                wrap=_nearest_branch(wrap_tree, path),
            )

        output_tree = DataTree({path: Branch(path, items) for path, items in output_branches.items()})
        return ComponentResult(output_tree, {"list": output_tree})

    def generate(self, list=None, indices=0, wrap=False):
        branch = list if isinstance(list, builtins.list) else [list]
        if not branch:
            return []

        raw_indices = indices if isinstance(indices, builtins.list) else [indices]
        raw_wrap = wrap if isinstance(wrap, builtins.list) else [wrap]
        wrap_enabled = bool(raw_wrap[0]) if raw_wrap else False
        count = len(branch)
        culled = {
            int(index) % count if wrap_enabled else int(index)
            for index in raw_indices
            if wrap_enabled or 0 <= int(index) < count
        }
        return [item for index, item in enumerate(branch) if index not in culled]
