"""Run components in tests and drive table-driven cases.

``run_component`` returns every output as a DataTree keyed by name.
``TableDrivenComponentTests`` runs a list of ``ComponentCase`` records as
subtests so one failing case does not hide the others.
"""

from __future__ import annotations

import builtins
import unittest
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any

from pyhopper.Core.Component import Component, ComponentResult
from pyhopper.Core.DataTree import DataTree

from tests.support.trees import assert_tree_equal, assert_tree_shape, is_tree_spec, item_from_json, spec_to_tree


def resolve_component(dotted: str) -> type[Component]:
    """Import ``pyhopper.Components.Tab.Sub.Module.Class``."""
    module_name, _, class_name = dotted.rpartition(".")
    component_cls = getattr(import_module(module_name), class_name)
    if not isinstance(component_cls, type) or not issubclass(component_cls, Component):
        raise TypeError(f"{dotted} is not a pyhopper Component")
    return component_cls


def decode_input(spec: Any) -> Any:
    """Golden-file input -> Python value.

    Atom JSON objects become atoms, path-keyed dicts become DataTrees, lists
    become single-branch trees (items decoded), scalars stay scalars. A list of
    lists (or of path-keyed dicts) is the spelling for a variadic port: one
    tree per stream, e.g. ``"streams": [["a", "b"], ["x"]]``.
    """
    if is_tree_spec(spec):
        return spec_to_tree(spec)
    if isinstance(spec, dict) and isinstance(spec.get("type"), str):
        return item_from_json(spec)
    if isinstance(spec, list):
        if spec and all(isinstance(item, list) or is_tree_spec(item) for item in spec):
            return [decode_input(item) for item in spec]
        return DataTree.from_list([item_from_json(item) for item in spec])
    return spec


def outputs_of(result: ComponentResult) -> dict[str, DataTree]:
    names = result.output_names or ["result"]
    return {name: result.output(name) for name in names}


def run_component(component_cls: type[Component], *args: Any, settings: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, DataTree]:
    """Call a component and return ``{output_name: DataTree}``."""
    if settings is not None:
        kwargs["_settings"] = settings
    return outputs_of(component_cls(*args, **kwargs))


@dataclass
class ComponentCase:
    """One table-driven case; ``inputs``/``expected`` use golden-file specs."""

    name: str
    inputs: dict[str, Any] = field(default_factory=dict)
    expected: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] | None = None
    raises: str | None = None
    shape_only: bool = False
    places: int = 7


def run_case(testcase: unittest.TestCase, component_cls: type[Component], case: ComponentCase) -> None:
    kwargs = {name: decode_input(spec) for name, spec in case.inputs.items()}
    if case.raises:
        exception = getattr(builtins, case.raises, None) or Exception
        with testcase.assertRaises(exception, msg=f"{case.name}: expected {case.raises}"):
            run_component(component_cls, settings=case.settings, **kwargs)
        return

    outputs = run_component(component_cls, settings=case.settings, **kwargs)
    for output_name, expected in case.expected.items():
        testcase.assertIn(output_name, outputs, f"{case.name}: component has no output '{output_name}'")
        if case.shape_only:
            assert_tree_shape(testcase, outputs[output_name], expected, msg=f"{case.name}.{output_name}")
        else:
            assert_tree_equal(testcase, outputs[output_name], spec_to_tree(expected), places=case.places, msg=f"{case.name}.{output_name}")


class TableDrivenComponentTests(unittest.TestCase):
    """Subclass, set ``component`` and ``cases``; each case runs as a subtest."""

    component: type[Component] | None = None
    cases: list[ComponentCase] = []

    def test_cases(self) -> None:
        if self.component is None:
            self.skipTest("abstract table-driven test")
        for case in self.cases:
            with self.subTest(case=case.name):
                run_case(self, self.component, case)
