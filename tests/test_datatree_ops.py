"""DataTree tree operations follow Grasshopper (rules pinned by rhino-test/oracle/cases/Sets/*Tree*.json)."""

from __future__ import annotations

import unittest

from tests.support.trees import assert_tree_equal, tree

from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path


class GraftFlattenTests(unittest.TestCase):
    def test_graft_keeps_empty_branches_as_empty_sub_branches(self):
        assert_tree_equal(self, tree({"0": ["a", "b"], "5": []}).graft(), {"0;0": ["a"], "0;1": ["b"], "5;0": []})

    def test_flatten_to_default_and_custom_path(self):
        source = tree({"0;0": ["a"], "1": ["b"], "2": []})
        assert_tree_equal(self, source.flatten(), {"0": ["a", "b"]})
        assert_tree_equal(self, source.flatten(Path(2, 3)), {"2;3": ["a", "b"]})

    def test_coerce_treats_a_path_as_one_item(self):
        coerced = DataTree.coerce(Path(2, 3))
        self.assertEqual(coerced.all_items(), [Path(2, 3)])


class SimplifyTests(unittest.TestCase):
    def test_removes_every_shared_position(self):
        assert_tree_equal(self, tree({"0;0;5": ["a"], "0;1;5": ["b"]}).simplify(), {"0": ["a"], "1": ["b"]})
        assert_tree_equal(self, tree({"0;7;1": ["a"], "1;7;2": ["b"]}).simplify(), {"0;1": ["a"], "1;2": ["b"]})

    def test_front_only_removes_the_leading_run(self):
        assert_tree_equal(self, tree({"0;0;5": ["a"], "0;1;5": ["b"]}).simplify(front=True), {"0;5": ["a"], "1;5": ["b"]})
        assert_tree_equal(self, tree({"0;7;1": ["a"], "1;7;2": ["b"]}).simplify(front=True), {"0;7;1": ["a"], "1;7;2": ["b"]})

    def test_single_branch_is_unchanged(self):
        assert_tree_equal(self, tree({"0;3;2": ["a"]}).simplify(), {"0;3;2": ["a"]})
        assert_tree_equal(self, tree({"0;0": ["a"]}).simplify(), {"0;0": ["a"]})

    def test_shortest_path_keeps_its_first_index(self):
        assert_tree_equal(self, tree({"2;1": ["a"], "2;1;0": ["b"]}).simplify(), {"2": ["a"], "2;0": ["b"]})
        assert_tree_equal(self, tree({"0": ["a"], "0;1": ["b"]}).simplify(), {"0": ["a"], "0;1": ["b"]})
        assert_tree_equal(self, tree({"2;1;3": ["a"], "2;1;3;0": ["b"]}).simplify(), {"2": ["a"], "2;0": ["b"]})


class TrimFlipTests(unittest.TestCase):
    def test_trim_removes_trailing_indices_and_drops_short_branches(self):
        source = tree({"0;0;1": ["a"], "0;0;2": ["b"], "0;1;0": ["c"], "3": ["d"]})
        assert_tree_equal(self, source.trim(1), {"0;0": ["a", "b"], "0;1": ["c"]})
        assert_tree_equal(self, source.trim(2), {"0": ["a", "b", "c"]})
        assert_tree_equal(self, source.trim(0), source)
        with self.assertRaises(ValueError):
            source.trim(-1)

    def test_flip_matrix_pads_and_varies_the_differing_index(self):
        assert_tree_equal(self, tree({"0": ["a", "b", "c"], "1": ["d", "e"]}).flip_matrix(), {"0": ["a", "d"], "1": ["b", "e"], "2": ["c", None]})
        assert_tree_equal(self, tree({"0;0": ["a", "b"], "1;0": ["c", "d"]}).flip_matrix(), {"0;0": ["a", "c"], "1;0": ["b", "d"]})
        assert_tree_equal(self, tree({"2;5;1": ["a", "b"], "2;5;3": ["c", "d"]}).flip_matrix(), {"2;5;0": ["a", "c"], "2;5;1": ["b", "d"]})
        assert_tree_equal(self, tree({"3": ["a", "b"]}).flip_matrix(), {"0": ["a"], "1": ["b"]})
        self.assertEqual(tree({"0": [], "1": []}).flip_matrix().branch_count, 0)

    def test_flip_matrix_rejects_uneven_or_multi_locus_paths(self):
        with self.assertRaises(ValueError):
            tree({"0;0": ["a"], "1": ["b"]}).flip_matrix()
        with self.assertRaises(ValueError):
            tree({"0;0": ["a"], "1;1": ["b"]}).flip_matrix()


class PruneCleanEntwineTests(unittest.TestCase):
    def test_prune_by_item_count(self):
        source = tree({"0": ["a"], "1": ["b", "c"], "2": [], "3": ["d", "e", "f"]})
        assert_tree_equal(self, source.prune(), source)
        assert_tree_equal(self, source.prune(minimum=2), {"1": ["b", "c"], "3": ["d", "e", "f"]})
        assert_tree_equal(self, source.prune(maximum=2), {"0": ["a"], "1": ["b", "c"], "2": []})

    def test_clean_nulls_invalid_and_empty(self):
        source = tree({"0": ["a", None, float("nan")], "1": [], "2": [None]})
        assert_tree_equal(self, source.clean(), {"0": ["a"], "1": [], "2": []})
        assert_tree_equal(self, source.clean(remove_empty=True), {"0": ["a"]})
        kept = source.clean(remove_nulls=False, remove_invalid=False)
        self.assertEqual(len(kept.branch(Path(0))), 3)

    def test_entwine_flattens_each_stream_into_its_own_branch(self):
        result = DataTree.entwine(tree({"3;1": ["a"], "3;2": ["b"]}), tree(["c"]))
        assert_tree_equal(self, result, {"0;0": ["a", "b"], "0;1": ["c"]})


if __name__ == "__main__":
    unittest.main()
