"""Merge - Merge multiple DataTrees into one (Sets > Tree)."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


class Merge(Component):
    """Merge any number of DataTrees into a single DataTree.

    Branches on the same path have their items concatenated, while unique
    branches are carried over unchanged. This mirrors Grasshopper's Merge
    component: ``data`` is a variadic TREE input, so ``Merge(a, b, c)`` and
    ``Merge(data=[a, b, c])`` are equivalent and receive every stream whole.
    """

    display_name = "Merge"
    nickname = "Merge"
    gh_guid = "3cadddef-1e2b-4c09-9390-0e8f78f7609f"

    inputs = [InputParam("data", None, Access.TREE, optional=True)]
    outputs = [OutputParam("result")]
    variadic_inputs = True

    def generate(self, data=()):
        return DataTree.merge(*data)
