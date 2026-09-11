"""Semantics of the Component solve pipeline (per-input access, Grasshopper rules).

These tests use tiny throw-away components so the rules are checked
independently of any real component: branch pairing, longest-list item
matching, LIST inputs as whole branches, TREE inputs passed whole, list
results sub-branching, ``NO_OUTPUT``, ``sub_branches`` and variadic streams.
"""

from __future__ import annotations

import unittest

from tests.support.trees import assert_tree_equal, tree

from pyhopper.Core.Component import Access, Component, InputParam, IterationContext, OutputParam
from pyhopper.Core.DataTree import DataTree, MatchRule
from pyhopper.Core.Path import Path


class _Add(Component):
    """Add two numbers (ITEM + ITEM)."""

    inputs = [InputParam("a", float, Access.ITEM), InputParam("b", float, Access.ITEM, default=0.0)]
    outputs = [OutputParam("result", float)]

    def generate(self, a=0.0, b=0.0):
        return a + b


class _Pick(Component):
    """Pick items by index (LIST + ITEM)."""

    inputs = [InputParam("list", None, Access.LIST), InputParam("index", int, Access.ITEM, default=0)]
    outputs = [OutputParam("item")]

    def generate(self, list=None, index=0):
        if not list or index < 0 or index >= len(list):
            return Component.NO_OUTPUT
        return list[index]


class _Repeat(Component):
    """Repeat a whole list *count* times (LIST + ITEM, list result)."""

    inputs = [InputParam("list", None, Access.LIST), InputParam("count", int, Access.ITEM, default=1)]
    outputs = [OutputParam("items")]

    def generate(self, list=None, count=1):
        return builtins_list(list or []) * int(count)


def builtins_list(value):
    return [item for item in value]


class _Chunks(Component):
    """Partition a list into pairs, one sub-branch per chunk."""

    inputs = [InputParam("list", None, Access.LIST)]
    outputs = [OutputParam("chunks")]

    def generate(self, list=None):
        items = list or []
        return self.sub_branches([items[i : i + 2] for i in range(0, len(items), 2)] or [[]])


class _BranchCount(Component):
    """Count branches of a whole tree (TREE)."""

    inputs = [InputParam("tree", None, Access.TREE)]
    outputs = [OutputParam("count", int)]

    def generate(self, tree=None):
        return tree.branch_count


class _Relocate(Component):
    """Move every item of a tree to a branch given per ITEM (TREE + ITEM, DataTree result)."""

    inputs = [InputParam("tree", None, Access.TREE), InputParam("target", int, Access.ITEM)]
    outputs = [OutputParam("result")]

    def generate(self, tree=None, target=0):
        return DataTree.from_branches({Path(target): tree.all_items()})


class _Context(Component):
    """Report the iteration context."""

    inputs = [InputParam("value", None, Access.ITEM)]
    outputs = [OutputParam("path", str), OutputParam("index", int), OutputParam("count", int)]

    def generate(self, value=None):
        ctx = self.iteration
        return str(ctx.path), ctx.index, ctx.count


class _Constant(Component):
    """Zero-input component."""

    inputs = []
    outputs = [OutputParam("value", float)]

    def generate(self):
        return 42.0


class _Weave(Component):
    """Variadic LIST streams: interleave first items of every stream."""

    inputs = [InputParam("pattern", int, Access.LIST, default=[0]), InputParam("streams", None, Access.LIST, optional=True)]
    outputs = [OutputParam("result")]
    variadic_inputs = True

    def generate(self, pattern=None, streams=()):
        return [stream[0] for stream in streams if stream]


class _Cross(Component):
    inputs = [InputParam("a", float, Access.ITEM), InputParam("b", float, Access.ITEM)]
    outputs = [OutputParam("result", float)]
    match_rule = MatchRule.CROSS_REFERENCE

    def generate(self, a=0.0, b=0.0):
        return a + b


class _Optional(Component):
    inputs = [InputParam("a", float, Access.ITEM), InputParam("b", float, Access.ITEM, optional=True)]
    outputs = [OutputParam("result", str)]

    def generate(self, a=0.0, b=None):
        return f"{a}:{b}"


class ItemMatchingTests(unittest.TestCase):
    def test_item_inputs_repeat_last_item(self):
        assert_tree_equal(self, _Add(tree([1, 2, 3]), tree([10])), {"0": [11, 12, 13]})

    def test_list_input_whole_branch_item_input_iterated(self):
        result = _Pick(tree(["a", "b", "c", "d"]), tree([0, 2, 3]))
        assert_tree_equal(self, result, {"0": ["a", "c", "d"]})

    def test_principal_is_tree_with_most_branches_then_deepest(self):
        lists = tree({"0": ["a", "b", "c", "d"], "2;1": [10, 20, 30], "5": []})
        result = _Pick(lists, tree([1]))
        assert_tree_equal(self, result, {"0": ["b"], "2;1": [20], "5": []})

    def test_item_tree_with_more_branches_becomes_principal(self):
        result = _Pick(tree(["a", "b", "c"]), tree({"0": [0], "1": [1]}))
        assert_tree_equal(self, result, {"0": ["a"], "1": ["b"]})

    def test_missing_paths_pair_with_last_branch(self):
        lists = tree({"0": ["a", "b"], "1": ["c", "d"], "2": ["e", "f"]})
        result = _Pick(lists, tree({"0": [0], "1": [1]}))
        assert_tree_equal(self, result, {"0": ["a"], "1": ["d"], "2": ["f"]})

    def test_multiple_item_iterations_with_list_results_create_sub_branches(self):
        two = _Repeat(tree(["x", "y"]), tree([1, 2]))
        assert_tree_equal(self, two, {"0;0": ["x", "y"], "0;1": ["x", "y", "x", "y"]})
        one = _Repeat(tree(["x", "y"]), tree([2]))
        assert_tree_equal(self, one, {"0": ["x", "y", "x", "y"]})

    def test_empty_required_item_branch_is_preserved_as_empty_output(self):
        result = _Add(tree({"0": [1, 2], "1": []}), tree({"0": [10], "1": [20]}))
        assert_tree_equal(self, result, {"0": [11, 12], "1": []})

    def test_optional_item_input_absent_or_empty_is_omitted_from_kwargs(self):
        assert_tree_equal(self, _Optional(tree([1.0])), {"0": ["1.0:None"]})
        result = _Optional(tree({"0": [1.0], "1": [2.0]}), tree({"0": [5.0], "1": []}))
        assert_tree_equal(self, result, {"0": ["1.0:5.0"], "1": ["2.0:None"]})

    def test_shortest_list_rule_stops_at_shortest_input(self):
        class _Short(_Add):
            match_rule = MatchRule.SHORTEST_LIST

        assert_tree_equal(self, _Short(tree([1, 2, 3]), tree([10, 20])), {"0": [11, 22]})

    def test_cross_reference_rule_yields_sub_paths(self):
        result = _Cross(tree([1, 2]), tree([10, 20]))
        assert_tree_equal(self, result, {"0;0": [11, 21], "0;1": [12, 22]})


class TreeAccessTests(unittest.TestCase):
    def test_tree_input_is_passed_whole_once(self):
        assert_tree_equal(self, _BranchCount(tree({"0": [1], "3": [2], "4;1": [3]})), {"0": [3]})

    def test_tree_input_mixed_with_item_input_iterates_items_and_merges_absolute_paths(self):
        data = tree({"0": ["a"], "1": ["b"]})
        result = _Relocate(data, tree([7, 9]))
        assert_tree_equal(self, result, {"7": ["a", "b"], "9": ["a", "b"]})

    def test_datatree_results_merge_across_iterations(self):
        data = tree({"0": ["a"], "1": ["b"]})
        result = _Relocate(data, tree([5, 5]))
        assert_tree_equal(self, result, {"5": ["a", "b", "a", "b"]})


class OutputPlacementTests(unittest.TestCase):
    def test_no_output_sentinel_emits_nothing_but_keeps_branch_when_single_iteration(self):
        result = _Pick(tree(["a"]), tree([5]))
        assert_tree_equal(self, result, {"0": []})

    def test_no_output_for_some_iterations_only_drops_those(self):
        result = _Pick(tree(["a", "b"]), tree([0, 9, 1]))
        assert_tree_equal(self, result, {"0": ["a", "b"]})

    def test_sub_branches_helper_paths(self):
        result = _Chunks(tree({"0": [1, 2, 3], "5": []}))
        assert_tree_equal(self, result, {"0;0": [1, 2], "0;1": [3], "5;0": []})

    def test_sub_branches_include_iteration_index_when_count_exceeds_one(self):
        class _Split(Component):
            inputs = [InputParam("list", None, Access.LIST), InputParam("n", int, Access.ITEM)]
            outputs = [OutputParam("chunks")]

            def generate(self, list=None, n=1):
                return self.sub_branches([list[:n], list[n:]])

        result = _Split(tree([1, 2, 3]), tree([1, 2]))
        assert_tree_equal(self, result, {"0;0;0": [1], "0;0;1": [2, 3], "0;1;0": [1, 2], "0;1;1": [3]})

    def test_iteration_context_reports_path_index_count(self):
        result = _Context(tree({"2": ["a", "b"]}))
        assert_tree_equal(self, result.path, {"2": ["{2}", "{2}"]})
        assert_tree_equal(self, result.index, {"2": [0, 1]})
        assert_tree_equal(self, result.count, {"2": [2, 2]})
        self.assertIsInstance(_Context.iteration, type(None))

    def test_zero_input_component_outputs_at_root_path(self):
        assert_tree_equal(self, _Constant(), {"0": [42.0]})


class BindingTests(unittest.TestCase):
    def test_variadic_positional_and_keyword_forms_are_equivalent(self):
        a = tree({"0": ["a1", "a2"], "1": ["b1"]})
        b = tree({"0": ["c1"], "1": ["d1", "d2"]})
        positional = _Weave([0], a, b)
        keyword = _Weave(pattern=[0], streams=[a, b])
        assert_tree_equal(self, positional, {"0": ["a1", "c1"], "1": ["b1", "d1"]})
        assert_tree_equal(self, keyword, positional)

    def test_variadic_without_streams_omits_the_argument(self):
        assert_tree_equal(self, _Weave([0]), {"0": []})

    def test_extra_positional_or_unknown_keyword_raises_type_error(self):
        with self.assertRaises(TypeError):
            _Add(1.0, 2.0, 3.0)
        with self.assertRaises(TypeError):
            _Add(1.0, bogus=5.0)
        with self.assertRaises(TypeError):
            _Add(1.0, 2.0, a=3.0)

    def test_missing_required_input_raises_type_error(self):
        with self.assertRaises(TypeError):
            _Add()

    def test_defaults_are_bound_when_omitted(self):
        assert_tree_equal(self, _Add(tree([1.5])), {"0": [1.5]})


class DataTreeMatchTests(unittest.TestCase):
    def test_longest_list_match_returns_no_iterations_for_empty_branch(self):
        pairs = list(DataTree.match([tree({"0": [1, 2]}), tree({"0": []})]))
        self.assertEqual(len(pairs), 1)
        path, matched = pairs[0]
        self.assertEqual(matched, [[], []])

    def test_principal_and_nearest_branch(self):
        a = tree({"0": [1]})
        b = tree({"0": [1], "1": [2]})
        self.assertIs(DataTree.principal([a, b]), b)
        self.assertEqual(a.nearest_branch(Path(1)), [1])
        self.assertEqual(a.nearest_branch(Path(0)), [1])


if __name__ == "__main__":
    unittest.main()
