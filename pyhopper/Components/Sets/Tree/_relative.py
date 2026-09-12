"""Relative item pairing shared by Relative Item and Relative Items."""

from __future__ import annotations

from pyhopper.Core.DataTree import DataTree
from pyhopper.Utils.PathMasks import offset_path, parse_relative_offset


def relative_items(tree_a: DataTree, tree_b: DataTree | None, offset: str, wrap_paths: bool, wrap_items: bool) -> tuple[DataTree, DataTree]:
    """Pair every item of ``tree_a`` with the item ``offset`` away in ``tree_b`` (or in ``tree_a``)."""
    parsed = parse_relative_offset(offset)
    other = tree_a if tree_b is None else tree_b
    other_paths = list(other.paths)
    first, second = {}, {}
    for path in tree_a.paths:
        target = offset_path(path, parsed.path, other_paths, wrap_paths)
        if target is None:
            continue
        source, partner = list(tree_a.branch(path)), list(other.branch(target))
        if not source or not partner:
            continue
        items_a, items_b = [], []
        for index, item in enumerate(source):
            position = index + parsed.item
            if wrap_items:
                position %= len(partner)
            elif not 0 <= position < len(partner):
                continue
            items_a.append(item)
            items_b.append(partner[position])
        if items_a:
            first[path], second[path] = items_a, items_b
    return DataTree.from_branches(first), DataTree.from_branches(second)
