"""
Component - Base class for all pyhopper components.

Handles the entire solve pipeline: input binding and coercion, branch
pairing across inputs, per-input access (ITEM / LIST / TREE) iteration,
calling generate(), and output tree construction. Concrete components only
implement generate().

Access semantics follow Grasshopper:

* ``ITEM`` inputs are iterated item by item inside a branch (longest-list
  matching, last item repeated).
* ``LIST`` inputs are handed to ``generate()`` as the whole branch (a list),
  once per branch.
* ``TREE`` inputs do not take part in branch pairing; the full ``DataTree``
  is supplied to every call.
* With ``variadic_inputs = True`` the last declared input accepts any number
  of streams; ``generate()`` receives them as a list (one entry per stream,
  each shaped by the declared access).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import product
from typing import Any, Iterable, Sequence

from .TypeSystem import TypeSpec

from .Branch import Branch
from .DataTree import DataTree, MatchRule
from .Path import Path


# ── Input / Output descriptors ──────────────────────────────────────


class Access(Enum):
    ITEM = "item"   # generate called once per matched item-tuple
    LIST = "list"   # generate called once per matched branch
    TREE = "tree"   # generate receives the whole tree on every call


@dataclass
class InputParam:
    name: str
    type_hint: type | TypeSpec | None = None
    access: Access = Access.ITEM
    default: Any = None
    optional: bool = False


@dataclass
class OutputParam:
    """An output port. ``access`` mirrors Grasshopper's output access: on a
    component that iterates items, ``LIST`` outputs keep their
    ``{path;iteration}`` sub-branch even when they emit nothing; ``ITEM`` and
    ``TREE`` outputs keep the branch path."""

    name: str
    type_hint: type | TypeSpec | None = None
    access: Access = Access.ITEM


# ── Sentinels and iteration context ─────────────────────────────────


class _NoOutput:
    """Returned from generate() (or as one tuple element) to emit nothing."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "NO_OUTPUT"


NO_OUTPUT = _NoOutput()


@dataclass(frozen=True)
class IterationContext:
    """Where the current generate() call writes: branch path, item index, item count."""

    path: Path
    index: int = 0
    count: int = 1


@dataclass
class _BoundInput:
    param: InputParam
    tree: DataTree
    stream_index: int | None = None  # set for variadic streams


@dataclass
class _BoundInputs:
    tree_inputs: list[_BoundInput] = field(default_factory=list)
    iterated: list[_BoundInput] = field(default_factory=list)   # ITEM + LIST, declaration order


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

    Inside ``generate()``:

    * ``self.iteration`` tells the current branch path, item index and count.
    * return ``Component.NO_OUTPUT`` (or use it as one tuple element) to emit
      nothing for this call.
    * return a ``list`` to emit several items. Like Grasshopper's
      ``SetDataList``, the list lands in the sub-branch ``{path;iteration}``
      when the component iterates items (it has an ITEM input: one curve at
      ``{0}`` divides into points at ``{0;0}``), and directly in ``{path}``
      when every input is LIST or TREE access (Mass Addition's partial
      results, Dispatch, Weave — one call per branch, no iteration index).
    * return a ``DataTree`` to place items at absolute paths; use
      ``self.sub_branches(lists)`` to build one under the current branch.

    Declare ``OutputParam(..., access=Access.LIST)`` for outputs that emit
    lists so an empty or silent iteration still leaves its list branch
    behind, exactly as Grasshopper does.

    Interactive components describe the data a person authors on the node
    declaratively so the studio and the graph compiler never special-case a
    class by name:

    * ``settings_schema`` — call-time ``_settings`` (a slider's range and
      rounding); the base class merges them with their defaults.
    * ``authored_values`` — per-node values the compiler bakes into the
      generated source (a toggle's state, a panel's text). Each spec is
      ``{"type": float | int | bool | string | choice | list, "default": ...}``
      plus optional ``choices``, ``min``, ``max`` and ``label``.
    * ``authored_emit`` — the compiler strategy that turns authored values
      into code (``"literal"``, ``"vector"``, ``"panel"``, ``"graph_mapper"``,
      ``"settings"``). ``None`` means values that name an input are passed
      as literals when that input is not wired.
    """

    inputs: list[InputParam] = []
    outputs: list[OutputParam] = [OutputParam("result")]
    match_rule: MatchRule = MatchRule.LONGEST_LIST
    settings_schema: dict[str, dict[str, Any]] = {}
    authored_values: dict[str, dict[str, Any]] = {}
    authored_emit: str | None = None
    variadic_inputs: bool = False

    # Optional Grasshopper-facing metadata (surfaced by the catalog).
    display_name: str | None = None
    nickname: str | None = None
    gh_guid: str | None = None
    gh_extra_inputs: tuple[str, ...] = ()

    NO_OUTPUT = NO_OUTPUT
    iteration: IterationContext | None = None

    def __new__(cls, *args: Any, **kwargs: Any) -> ComponentResult:
        settings = kwargs.pop("_settings", None)
        instance = object.__new__(cls)
        instance.settings = instance._normalize_settings(settings)
        instance.iteration = None
        return instance._solve(*args, **kwargs)

    def _normalize_settings(self, settings: Any) -> dict[str, Any]:
        """Merge optional component settings with class defaults."""
        schema = getattr(type(self), "settings_schema", {}) or {}
        normalized = {
            key: spec.get("default")
            for key, spec in schema.items()
            if isinstance(spec, dict) and "default" in spec
        }
        if settings is None:
            return normalized
        if not isinstance(settings, dict):
            raise TypeError(f"{type(self).__name__} _settings must be a dictionary")

        for key, value in settings.items():
            if key not in schema:
                raise ValueError(f"{type(self).__name__} does not support setting '{key}'")
            normalized[key] = value
        return normalized

    @classmethod
    def authored_defaults(cls) -> dict[str, Any]:
        """Default of every authored value, in declaration order."""
        return {
            key: spec.get("default")
            for key, spec in cls.authored_values.items()
            if isinstance(spec, dict) and "default" in spec
        }

    @classmethod
    def validate_authored(cls, section: str, data: dict[str, Any]) -> list[tuple[str, str]]:
        """Cross-field checks the schemas cannot express.

        The graph compiler calls this once per node after the per-key type and
        choice checks pass, with ``section`` ``"values"`` or ``"settings"``.
        Return ``(key, message)`` pairs (an empty key addresses the section).
        """
        return []

    def generate(self, **kw: Any) -> Any:
        """Override in subclasses. Receives matched inputs as keyword args.

        Return a single value (single-output) or a tuple matching
        len(self.outputs) for multi-output components.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement generate()"
        )

    # ── Helpers available inside generate() ─────────────────────────

    def sub_branches(self, lists: Iterable[Iterable[Any]], *, iteration: bool = True) -> DataTree:
        """Build a tree with one branch per list under the current branch.

        Branch ``k`` lands at ``{path;k}`` for a component that runs once per
        branch (LIST/TREE inputs only, like Partition List), or at
        ``{path;index;k}`` under the iteration's own sub-branch when the
        component iterates items. Pass ``iteration=False`` for Grasshopper
        components that append only the group index to the branch path even
        though they iterate (Point Groups); iterations then share ``{path;k}``.
        """
        context = self.iteration or IterationContext(Path.root())
        base = context.path.append(context.index) if iteration and self._iterates_items() else context.path
        branches: dict[Path, list[Any]] = {}
        for k, items in enumerate(lists):
            branches[base.append(k)] = list(items)
        return DataTree.from_branches(branches)

    def _iterates_items(self) -> bool:
        """True when an ITEM input makes the component iterate inside each branch.

        Grasshopper appends the iteration index to list outputs only for such
        components; a component whose inputs are all LIST/TREE access runs once
        per branch and writes lists straight into the branch path.
        """
        return any(param.access == Access.ITEM for param in self.inputs)

    # ── Input binding ───────────────────────────────────────────────

    def _variadic_index(self) -> int | None:
        if self.variadic_inputs and self.inputs:
            return len(self.inputs) - 1
        return None

    def _bind_inputs(self, *args: Any, **kwargs: Any) -> _BoundInputs:
        """Map positional/keyword args to declared inputs and coerce them."""
        params = list(self.inputs)
        params_by_name = {param.name: param for param in params}
        variadic_index = self._variadic_index()
        variadic_name = params[variadic_index].name if variadic_index is not None else None
        name = type(self).__name__

        bound: list[_BoundInput] = []
        seen: set[str] = set()
        streams = 0

        for index, arg in enumerate(args):
            if variadic_index is not None and index >= variadic_index:
                param = params[variadic_index]
                bound.append(_BoundInput(param, self._coerce_input_tree(param, DataTree.coerce(arg)), streams))
                streams += 1
            elif index < len(params):
                param = params[index]
                bound.append(_BoundInput(param, self._coerce_input_tree(param, DataTree.coerce(arg))))
            else:
                raise TypeError(
                    f"{name} accepts {len(params)} positional input(s) but {len(args)} were given"
                )
            seen.add(param.name)

        for key, value in kwargs.items():
            param = params_by_name.get(key)
            if param is None:
                raise TypeError(f"{name} got an unexpected input '{key}'")
            if key in seen:
                raise TypeError(f"{name} got multiple values for input '{key}'")
            if param.name == variadic_name:
                for stream in self._variadic_streams(value):
                    bound.append(_BoundInput(param, self._coerce_input_tree(param, DataTree.coerce(stream)), streams))
                    streams += 1
            else:
                bound.append(_BoundInput(param, self._coerce_input_tree(param, DataTree.coerce(value))))
            seen.add(key)

        for param in params:
            if param.name in seen:
                continue
            if param.default is not None:
                tree = self._coerce_input_tree(param, DataTree.coerce(param.default))
                bound.append(_BoundInput(param, tree, 0 if param.name == variadic_name else None))
            elif not param.optional and param.name != variadic_name:
                raise TypeError(f"{name} missing required input: '{param.name}'")

        result = _BoundInputs()
        for item in bound:
            if item.param.access == Access.TREE:
                result.tree_inputs.append(item)
            else:
                result.iterated.append(item)
        return result

    @staticmethod
    def _variadic_streams(value: Any) -> list[Any]:
        """A list/tuple of DataTrees is a stream collection; anything else is one stream."""
        if isinstance(value, (list, tuple)) and value and all(isinstance(item, DataTree) for item in value):
            return list(value)
        return [value]

    def _coerce_inputs(self, *args: Any, **kwargs: Any) -> dict[str, DataTree | list[DataTree]]:
        """Compatibility helper: bound inputs as ``{name: tree}`` (variadic → list of trees)."""
        bound = self._bind_inputs(*args, **kwargs)
        result: dict[str, Any] = {}
        for item in bound.tree_inputs + bound.iterated:
            if item.stream_index is not None:
                result.setdefault(item.param.name, []).append(item.tree)
            else:
                result[item.param.name] = item.tree
        return result

    @staticmethod
    def _coerce_input_tree(param: InputParam, tree: DataTree) -> DataTree:
        """Apply framework-level typed input conversions while preserving paths."""
        from .TypeSystem import coerce_tree

        return coerce_tree(tree, param.type_hint, input_name=param.name)

    # ── Solve pipeline ──────────────────────────────────────────────

    def _solve(self, *args: Any, **kwargs: Any) -> ComponentResult:
        bound = self._bind_inputs(*args, **kwargs)
        collectors: list[dict[Path, list[Any]]] = [{} for _ in self.outputs]
        tree_kwargs = self._group_values([(item.param, item.tree, item.stream_index) for item in bound.tree_inputs])

        if not bound.iterated:
            # Zero-input component, or every input is TREE access: one call at {0}.
            touched = self._run_generate(tree_kwargs, Path.root(), 0, 1, collectors)
            self._keep_topology(Path.root(), collectors, touched)
            return self._build_result(collectors)

        principal = DataTree.principal([item.tree for item in bound.iterated])
        for path in principal.paths:
            branches = [item.tree.nearest_branch(path) for item in bound.iterated]
            self._solve_branch(bound, path, branches, tree_kwargs, collectors)

        return self._build_result(collectors)

    def _solve_branch(
        self,
        bound: _BoundInputs,
        path: Path,
        branches: list[list[Any]],
        tree_kwargs: dict[str, Any],
        collectors: list[dict[Path, list[Any]]],
    ) -> None:
        list_values: list[tuple[InputParam, Any, int | None]] = []
        item_specs: list[tuple[_BoundInput, list[Any]]] = []
        for item, branch in zip(bound.iterated, branches):
            if item.param.access == Access.LIST:
                list_values.append((item.param, list(branch), item.stream_index))
            else:
                item_specs.append((item, branch))

        active_items = [(item, branch) for item, branch in item_specs if branch]
        missing_required = any(not branch and not item.param.optional for item, branch in item_specs)

        if missing_required:
            indices: list[tuple[int, ...]] = []
        elif not active_items:
            indices = [()]
        else:
            indices = list(_iteration_indices([len(branch) for _, branch in active_items], self.match_rule))

        count = len(indices)
        touched = [False] * len(collectors)
        for iteration_index, combo in enumerate(indices):
            values = list(list_values)
            for (item, branch), item_index in zip(active_items, combo):
                values.append((item.param, branch[item_index], item.stream_index))
            kwargs = dict(tree_kwargs)
            kwargs.update(self._group_values(values))
            target = path
            if self.match_rule == MatchRule.CROSS_REFERENCE and combo:
                target = path.append(combo[0])
            for output_index, did_touch in enumerate(self._run_generate(kwargs, target, iteration_index, count, collectors)):
                touched[output_index] = touched[output_index] or did_touch
        self._keep_topology(path, collectors, touched)

    def _keep_topology(self, path: Path, collectors: list[dict[Path, list[Any]]], touched: list[bool]) -> None:
        """An empty or silent branch stays a (sub-)branch, per output, like Grasshopper.

        ITEM and TREE outputs keep ``{path}``; LIST outputs keep their list path —
        ``{path;0}`` (the missing first iteration) on an item-iterating component,
        ``{path}`` otherwise.
        """
        for out_param, collector, did_touch in zip(self.outputs, collectors, touched):
            if not did_touch:
                collector.setdefault(self._list_path(path, 0) if out_param.access == Access.LIST else path, [])

    def _list_path(self, path: Path, index: int) -> Path:
        """Where a list emitted at iteration ``index`` of ``path`` lands."""
        return path.append(index) if self._iterates_items() else path

    @staticmethod
    def _group_values(values: Sequence[tuple[InputParam, Any, int | None]]) -> dict[str, Any]:
        """Turn (param, value, stream_index) triples into generate() kwargs."""
        grouped: dict[str, Any] = {}
        streams: dict[str, list[tuple[int, Any]]] = {}
        for param, value, stream_index in values:
            if stream_index is None:
                grouped[param.name] = value
            else:
                streams.setdefault(param.name, []).append((stream_index, value))
        for name, entries in streams.items():
            grouped[name] = [value for _, value in sorted(entries, key=lambda entry: entry[0])]
        return grouped

    def _run_generate(
        self,
        kwargs: dict[str, Any],
        path: Path,
        index: int,
        count: int,
        collectors: list[dict[Path, list[Any]]],
    ) -> list[bool]:
        """Call generate() once and collect its outputs; one flag per output says whether it touched its tree."""
        self.iteration = IterationContext(path, index, count)
        result = self.generate(**kwargs)
        return self._collect(result, path, index, count, collectors)

    # ── Output collection ───────────────────────────────────────────

    def _collect(
        self,
        result: Any,
        path: Path,
        index: int,
        count: int,
        collectors: list[dict[Path, list[Any]]],
    ) -> list[bool]:
        num_outputs = len(self.outputs)
        if num_outputs > 1:
            if not isinstance(result, (tuple, list)) or len(result) != num_outputs:
                raise ValueError(
                    f"{type(self).__name__}.generate() must return a tuple of "
                    f"{num_outputs} elements (matching {num_outputs} outputs), "
                    f"got {type(result).__name__}"
                )
            values = list(result)
        else:
            values = [result]

        list_path = self._list_path(path, index)
        return [
            self._place_value(collector, path, list_path, value, out_param.access)
            for out_param, collector, value in zip(self.outputs, collectors, values)
        ]

    @staticmethod
    def _place_value(
        collector: dict[Path, list[Any]],
        path: Path,
        list_path: Path,
        value: Any,
        access: Access,
    ) -> bool:
        """Route one generate() value into a collector; True when the tree was touched.

        * ``NO_OUTPUT`` places nothing — except that a LIST-access output keeps
          its empty list path (Grasshopper leaves the iteration's list branch
          behind when a component emits nothing).
        * ``DataTree`` results are merged at their absolute paths.
        * ``list`` results go to ``list_path`` (``{path;iteration}`` on an
          item-iterating component, ``{path}`` otherwise).
        * anything else is appended as a single item at ``{path}``.
        """
        if value is NO_OUTPUT:
            if access == Access.LIST:
                collector.setdefault(list_path, [])
                return True
            return False
        if isinstance(value, DataTree):
            for branch_path, branch in value.branches():
                collector.setdefault(branch_path, []).extend(branch)
            return True
        if isinstance(value, list):
            collector.setdefault(list_path, []).extend(value)
            return True
        collector.setdefault(path, []).append(value)
        return True

    def _build_result(self, collectors: list[dict[Path, list[Any]]]) -> ComponentResult:
        """Build ComponentResult from output branch collectors."""
        output_trees: dict[str, DataTree] = {}
        for out_param, collector in zip(self.outputs, collectors):
            branches = {path: Branch(path, items) for path, items in collector.items()}
            output_trees[out_param.name] = DataTree(branches)

        primary = output_trees[self.outputs[0].name]
        return ComponentResult(primary, output_trees)


# ── Item matching inside a branch ───────────────────────────────────


def _iteration_indices(lengths: Sequence[int], rule: MatchRule) -> Iterable[tuple[int, ...]]:
    """Yield one index tuple (one index per ITEM input) for every iteration."""
    if not lengths or any(length <= 0 for length in lengths):
        return
    if rule == MatchRule.SHORTEST_LIST:
        for i in range(min(lengths)):
            yield tuple(i for _ in lengths)
    elif rule == MatchRule.CROSS_REFERENCE:
        yield from product(*(range(length) for length in lengths))
    else:  # LONGEST_LIST: repeat the last item of shorter inputs
        for i in range(max(lengths)):
            yield tuple(min(i, length - 1) for length in lengths)
