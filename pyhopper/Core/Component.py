"""
Component - Base class for all pyhopper components.

Handles the entire solve pipeline: input coercion, data matching,
iteration over branches/items, calling generate(), and output tree
construction. Concrete components only implement generate().
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .Branch import Branch
from .DataTree import DataTree, MatchRule
from .Path import Path


# ── Input / Output descriptors ──────────────────────────────────────


class Access(Enum):
    ITEM = "item"   # generate called once per matched item-tuple
    LIST = "list"   # generate called once per matched branch
    TREE = "tree"   # generate called once with full trees


@dataclass
class InputParam:
    name: str
    type_hint: type | None = None
    access: Access = Access.ITEM
    default: Any = None
    optional: bool = False


@dataclass
class OutputParam:
    name: str
    type_hint: type | None = None


# ── ComponentResult ─────────────────────────────────────────────────


class ComponentResult(DataTree):
    """A DataTree (first output) that also carries sibling outputs.

    Returned by Component.__new__. Behaves exactly like a DataTree for
    the primary output, and exposes secondary outputs as attributes.
    """

    def __init__(
        self,
        primary: DataTree,
        all_outputs: dict[str, DataTree] | None = None,
    ) -> None:
        super().__init__(dict(primary._branches))
        self._all_outputs = all_outputs or {}

    def __getattr__(self, name: str) -> DataTree:
        if name.startswith("_"):
            raise AttributeError(name)
        outputs = object.__getattribute__(self, "_all_outputs")
        if name in outputs:
            return outputs[name]
        raise AttributeError(
            f"No output named '{name}'. Available: {list(outputs.keys())}"
        )

    @property
    def output_names(self) -> list[str]:
        return list(self._all_outputs.keys())

    def output(self, name: str) -> DataTree:
        """Access an output by name."""
        return self._all_outputs[name]


# ── Component base class ───────────────────────────────────────────


class Component:
    """Base class for all pyhopper components.

    Subclasses define:
        inputs  = [InputParam(...), ...]
        outputs = [OutputParam(...), ...]

        def generate(self, **matched_inputs) -> value | tuple

    Calling MyComponent(arg1, arg2, kwarg=val) triggers the solve
    pipeline and returns a ComponentResult (a DataTree).
    """

    inputs: list[InputParam] = []
    outputs: list[OutputParam] = [OutputParam("result")]
    match_rule: MatchRule = MatchRule.LONGEST_LIST

    def __new__(cls, *args: Any, **kwargs: Any) -> ComponentResult:
        instance = object.__new__(cls)
        return instance._solve(*args, **kwargs)

    def generate(self, **kw: Any) -> Any:
        """Override in subclasses. Receives matched items as keyword args.

        Return a single value (single-output) or a tuple matching
        len(self.outputs) for multi-output components.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement generate()"
        )

    # ── Solve pipeline ──────────────────────────────────────────────

    def _solve(self, *args: Any, **kwargs: Any) -> ComponentResult:
        # 1. Map args/kwargs to declared inputs
        input_trees = self._coerce_inputs(*args, **kwargs)

        # 2. Determine access mode (use the first input's access, or ITEM)
        access = self._get_access_mode()

        # 3. Dispatch based on access mode
        if access == Access.TREE:
            return self._solve_tree(input_trees)
        elif access == Access.LIST:
            return self._solve_list(input_trees)
        else:
            return self._solve_item(input_trees)

    def _coerce_inputs(self, *args: Any, **kwargs: Any) -> dict[str, DataTree]:
        """Map positional/keyword args to input names, coerce to DataTrees."""
        input_trees: dict[str, DataTree] = {}

        # Positional args map to inputs in declaration order
        for i, arg in enumerate(args):
            if i < len(self.inputs):
                name = self.inputs[i].name
                input_trees[name] = DataTree.coerce(arg)

        # Keyword args override
        for key, val in kwargs.items():
            input_trees[key] = DataTree.coerce(val)

        # Fill defaults for missing inputs
        for inp in self.inputs:
            if inp.name not in input_trees:
                if inp.default is not None:
                    input_trees[inp.name] = DataTree.coerce(inp.default)
                elif not inp.optional:
                    raise TypeError(
                        f"{type(self).__name__} missing required input: '{inp.name}'"
                    )

        return input_trees

    def _get_access_mode(self) -> Access:
        """Determine the access mode from input declarations."""
        if not self.inputs:
            return Access.ITEM
        # If any input uses TREE access, use TREE
        for inp in self.inputs:
            if inp.access == Access.TREE:
                return Access.TREE
        # If any input uses LIST access, use LIST
        for inp in self.inputs:
            if inp.access == Access.LIST:
                return Access.LIST
        return Access.ITEM

    # ── ITEM access solve ───────────────────────────────────────────

    def _solve_item(self, input_trees: dict[str, DataTree]) -> ComponentResult:
        """Solve with ITEM access: generate called once per matched item-tuple."""
        if not input_trees:
            # Zero-input component
            return self._build_result_from_single_call({})

        input_names = [inp.name for inp in self.inputs if inp.name in input_trees]
        trees = [input_trees[name] for name in input_names]

        # Initialize output collectors
        output_branches: list[dict[Path, list]] = [
            {} for _ in self.outputs
        ]

        for path, matched_items in DataTree.match(trees, self.match_rule):
            # matched_items[i] is a list of items from trees[i]
            num_items = len(matched_items[0]) if matched_items else 0

            for item_idx in range(num_items):
                kw = {}
                for j, name in enumerate(input_names):
                    kw[name] = matched_items[j][item_idx]

                result = self.generate(**kw)
                self._collect_output(result, path, output_branches)

        return self._build_result(output_branches)

    # ── LIST access solve ───────────────────────────────────────────

    def _solve_list(self, input_trees: dict[str, DataTree]) -> ComponentResult:
        """Solve with LIST access: generate called once per matched branch."""
        if not input_trees:
            return self._build_result_from_single_call({})

        input_names = [inp.name for inp in self.inputs if inp.name in input_trees]
        trees = [input_trees[name] for name in input_names]

        output_branches: list[dict[Path, list]] = [
            {} for _ in self.outputs
        ]

        for path, matched_items in DataTree.match(trees, self.match_rule):
            kw = {}
            for j, name in enumerate(input_names):
                kw[name] = matched_items[j]  # pass the whole list

            result = self.generate(**kw)
            self._collect_output(result, path, output_branches)

        return self._build_result(output_branches)

    # ── TREE access solve ───────────────────────────────────────────

    def _solve_tree(self, input_trees: dict[str, DataTree]) -> ComponentResult:
        """Solve with TREE access: generate called once with full trees."""
        kw = {name: tree for name, tree in input_trees.items()}
        result = self.generate(**kw)

        output_branches: list[dict[Path, list]] = [
            {} for _ in self.outputs
        ]
        self._collect_output(result, Path.root(), output_branches)
        return self._build_result(output_branches)

    # ── Output collection helpers ───────────────────────────────────

    def _collect_output(
        self,
        result: Any,
        path: Path,
        output_branches: list[dict[Path, list]],
    ) -> None:
        """Place generate() return value(s) into the output branch collectors."""
        num_outputs = len(self.outputs)

        if num_outputs > 1:
            # Multi-output: result must be a tuple/list matching output count
            if not isinstance(result, (tuple, list)) or len(result) != num_outputs:
                raise ValueError(
                    f"{type(self).__name__}.generate() must return a tuple of "
                    f"{num_outputs} elements (matching {num_outputs} outputs), "
                    f"got {type(result).__name__}"
                )
            for i, val in enumerate(result):
                self._add_to_branch(output_branches[i], path, val)
        else:
            # Single output
            self._add_to_branch(output_branches[0], path, result)

    @staticmethod
    def _add_to_branch(
        collector: dict[Path, list], path: Path, value: Any
    ) -> None:
        """Add a value (single item or list of items) to the branch collector."""
        if path not in collector:
            collector[path] = []

        if isinstance(value, list):
            collector[path].extend(value)
        elif isinstance(value, DataTree):
            # If generate returns a DataTree, merge it
            collector[path].extend(value.all_items())
        else:
            collector[path].append(value)

    def _build_result(
        self, output_branches: list[dict[Path, list]]
    ) -> ComponentResult:
        """Build ComponentResult from output branch collectors."""
        output_trees: dict[str, DataTree] = {}

        for i, out_param in enumerate(self.outputs):
            branches = {}
            for path, items in output_branches[i].items():
                branches[path] = Branch(path, items)
            output_trees[out_param.name] = DataTree(branches)

        first_name = self.outputs[0].name
        primary = output_trees[first_name]
        return ComponentResult(primary, output_trees)

    def _build_result_from_single_call(
        self, kw: dict[str, Any]
    ) -> ComponentResult:
        """Handle zero-input components."""
        result = self.generate(**kw)
        output_branches: list[dict[Path, list]] = [
            {} for _ in self.outputs
        ]
        self._collect_output(result, Path.root(), output_branches)
        return self._build_result(output_branches)
