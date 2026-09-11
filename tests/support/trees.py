"""DataTree builders and comparison helpers for tests.

``tree({"0": [1, 2], "2;1": [3]})`` builds a DataTree from Grasshopper-style
path strings; ``assert_tree_equal`` compares two trees path by path with a
numeric tolerance so atoms built from floating point math still match.
"""

from __future__ import annotations

import dataclasses
import math
import unittest
from typing import Any

from pyhopper.Core.Atoms import Atom, atom_from_json
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path


def path(spec: Any) -> Path:
    """Accept ``"{0;1}"``, ``"0;1"``, ``(0, 1)``, ``0`` or a Path."""
    if isinstance(spec, Path):
        return spec
    if isinstance(spec, int):
        return Path(spec)
    if isinstance(spec, (tuple, list)):
        return Path(*spec)
    return Path.parse(str(spec))


def tree(spec: Any) -> DataTree:
    """Build a DataTree from a dict of path -> items, a list (branch {0}), or a scalar."""
    if isinstance(spec, DataTree):
        return spec
    if isinstance(spec, dict):
        return DataTree.from_branches({path(key): list(items) for key, items in spec.items()})
    if isinstance(spec, (list, tuple)):
        return DataTree.from_list(list(spec))
    return DataTree.from_item(spec)


def tree_to_spec(value: DataTree) -> dict[str, list[Any]]:
    """Serialise a tree into the golden-file form: ``{"{0;1}": [json items]}``."""
    return {str(branch_path): [item_to_json(item) for item in branch] for branch_path, branch in value.branches()}


def spec_to_tree(spec: Any) -> DataTree:
    """Inverse of :func:`tree_to_spec`; decodes atoms and Paths inside branches."""
    if isinstance(spec, dict):
        return DataTree.from_branches({path(key): [item_from_json(item) for item in items] for key, items in spec.items()})
    if isinstance(spec, (list, tuple)):
        return DataTree.from_list([item_from_json(item) for item in spec])
    return DataTree.from_item(item_from_json(spec))


def item_to_json(item: Any) -> Any:
    if isinstance(item, Atom):
        return item.to_json()
    if isinstance(item, Path):
        return {"type": "Path", "indices": list(item)}
    if isinstance(item, (list, tuple)):
        return [item_to_json(value) for value in item]
    return item


def item_from_json(item: Any) -> Any:
    if isinstance(item, dict) and isinstance(item.get("type"), str):
        if item["type"] == "Path":
            return Path(*item.get("indices", []))
        return atom_from_json(item)
    if isinstance(item, list):
        return [item_from_json(value) for value in item]
    return item


def is_tree_spec(value: Any) -> bool:
    """A dict whose keys all parse as paths (and is not an atom JSON object)."""
    if not isinstance(value, dict) or not value or "type" in value:
        return False
    try:
        for key in value:
            path(key)
    except (TypeError, ValueError):
        return False
    return True


def items_close(actual: Any, expected: Any, places: int = 7) -> bool:
    """Structural equality with float tolerance; atoms compared field by field."""
    tolerance = 10.0 ** (-places)
    if isinstance(expected, bool) or isinstance(actual, bool):
        return type(actual) is type(expected) and actual == expected
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance)
    if isinstance(expected, Atom) or isinstance(actual, Atom):
        if type(actual) is not type(expected):
            return False
        for field in dataclasses.fields(expected):
            if not items_close(getattr(actual, field.name), getattr(expected, field.name), places):
                return False
        return True
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        return len(actual) == len(expected) and all(items_close(a, e, places) for a, e in zip(actual, expected))
    if isinstance(expected, dict) and isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(items_close(actual[k], expected[k], places) for k in expected)
    return actual == expected


def describe(value: Any, limit: int = 160) -> str:
    text = repr(value)
    return text if len(text) <= limit else f"{text[: limit - 3]}..."


def assert_tree_equal(
    testcase: unittest.TestCase,
    actual: DataTree,
    expected: Any,
    places: int = 7,
    msg: str = "",
) -> None:
    """Assert two trees have identical paths (in order) and tolerant-equal items."""
    expected_tree = tree(expected) if not isinstance(expected, DataTree) else expected
    prefix = f"{msg}: " if msg else ""
    testcase.assertEqual(
        [str(p) for p in actual.paths],
        [str(p) for p in expected_tree.paths],
        f"{prefix}branch paths differ",
    )
    for branch_path in expected_tree.paths:
        actual_items = list(actual.branch(branch_path))
        expected_items = list(expected_tree.branch(branch_path))
        testcase.assertEqual(
            len(actual_items),
            len(expected_items),
            f"{prefix}item count differs at {branch_path}: {describe(actual_items)} vs {describe(expected_items)}",
        )
        for index, (a, e) in enumerate(zip(actual_items, expected_items)):
            if not items_close(a, e, places):
                testcase.fail(f"{prefix}item {index} at {branch_path} differs: {describe(a)} != {describe(e)}")


def assert_tree_shape(
    testcase: unittest.TestCase,
    actual: DataTree,
    expected_counts: dict[str, int],
    msg: str = "",
) -> None:
    """Assert paths and per-branch item counts only (used for random components)."""
    prefix = f"{msg}: " if msg else ""
    testcase.assertEqual(
        [str(p) for p in actual.paths],
        [str(path(key)) for key in expected_counts],
        f"{prefix}branch paths differ",
    )
    for key, count in expected_counts.items():
        testcase.assertEqual(len(actual.branch(path(key))), count, f"{prefix}item count differs at {key}")
