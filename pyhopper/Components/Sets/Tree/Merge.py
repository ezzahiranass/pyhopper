"""Merge - Merge multiple DataTrees into one (Sets > Tree)."""

from pyhopper.Core.Component import Access, Component, ComponentResult, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class Merge(Component):
    """Merge any number of DataTrees into a single DataTree.

    Branches on the same path have their items concatenated, while unique
    branches are carried over unchanged. This mirrors Grasshopper's Merge
    component and accepts a variable number of positional arguments.
    """

    inputs = [InputParam("data", None, Access.TREE, optional=True)]
    outputs = [OutputParam("result")]
    variadic_inputs = True

    def __new__(cls, *args) -> ComponentResult:  # type: ignore[override]
        trees = [DataTree.coerce(a) for a in args]
        merged = DataTree.merge(*trees)
        return ComponentResult(merged, {"result": merged})
