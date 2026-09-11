"""List component behaviour locks (ported from pyhopper-web/api; extended by the per-input access work)."""
from __future__ import annotations

import unittest


from tests.support.trees import assert_tree_equal, tree

from pyhopper import (
    AtomicInterval,
    AtomicPoint,
    Interpolate,
    ListItem,
    ListLength,
    Merge,
    NurbsCurve,
    PartitionList,
    Polyline,
    ReverseList,
    ShiftList,
    SplitList,
    SubList,
)
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path as TreePath


class ListComponentTests(unittest.TestCase):
    def setUp(self):
        self.tree = DataTree.from_branches(
            {
                TreePath(0): ["a", "b", "c", "d"],
                TreePath(2, 1): [10, 20, 30],
                TreePath(5): [],
            }
        )

    def test_list_length_preserves_paths(self):
        result = ListLength(self.tree)

        self.assertEqual(result.paths, self.tree.paths)
        self.assertEqual(list(result.branch(TreePath(0))), [4])
        self.assertEqual(list(result.branch(TreePath(2, 1))), [3])
        self.assertEqual(list(result.branch(TreePath(5))), [0])

    def test_split_list_preserves_paths(self):
        indices = DataTree.from_branches(
            {
                TreePath(0): [2],
                TreePath(2, 1): [1],
                TreePath(5): [3],
            }
        )

        result = SplitList(self.tree, indices)

        # list outputs land one level down, at {path;iteration} (Grasshopper's SetDataList rule)
        self.assertEqual(result.paths, [path.append(0) for path in self.tree.paths])
        self.assertEqual(list(result.branch(TreePath(0, 0))), ["a", "b"])
        self.assertEqual(list(result.list_b.branch(TreePath(0, 0))), ["c", "d"])
        self.assertEqual(list(result.branch(TreePath(2, 1, 0))), [10])
        self.assertEqual(list(result.list_b.branch(TreePath(2, 1, 0))), [20, 30])
        self.assertEqual(list(result.branch(TreePath(5, 0))), [])
        self.assertEqual(list(result.list_b.branch(TreePath(5, 0))), [])

    def test_sub_list_preserves_paths_and_reports_indices(self):
        domains = DataTree.from_branches(
            {
                TreePath(0): [AtomicInterval(1, 2)],
                TreePath(2, 1): [AtomicInterval(2, 0)],
                TreePath(5): [AtomicInterval(0, 1)],
            }
        )

        result = SubList(self.tree, domains, False)

        self.assertEqual(result.paths, [path.append(0) for path in self.tree.paths])
        self.assertEqual(list(result.branch(TreePath(0, 0))), ["b", "c"])
        self.assertEqual(list(result.index.branch(TreePath(0, 0))), [1, 2])
        self.assertEqual(list(result.branch(TreePath(2, 1, 0))), [30, 20, 10])
        self.assertEqual(list(result.index.branch(TreePath(2, 1, 0))), [2, 1, 0])
        self.assertEqual(list(result.branch(TreePath(5, 0))), [])
        self.assertEqual(list(result.index.branch(TreePath(5, 0))), [])

    def test_sub_list_wraps_indices_per_branch(self):
        tree = DataTree.from_branches({TreePath(4, 2): ["a", "b", "c"]})

        result = SubList(tree, AtomicInterval(-1, 4), True)

        self.assertEqual(result.paths, [TreePath(4, 2, 0)])
        self.assertEqual(result.all_items(), ["c", "a", "b", "c", "a", "b"])
        self.assertEqual(result.index.all_items(), [2, 0, 1, 2, 0, 1])

    def test_split_list_clamps_out_of_range_indices(self):
        self.assertEqual(SplitList([1, 2, 3], -2).all_items(), [])
        self.assertEqual(SplitList([1, 2, 3], -2).list_b.all_items(), [1, 2, 3])
        self.assertEqual(SplitList([1, 2, 3], 9).all_items(), [1, 2, 3])
        self.assertEqual(SplitList([1, 2, 3], 9).list_b.all_items(), [])

    def test_shift_list_wraps_or_removes_items_per_branch(self):
        wrapped = ShiftList(self.tree, 1, True)
        unwrapped = ShiftList(self.tree, -1, False)

        self.assertEqual(list(wrapped.branch(TreePath(0, 0))), ["b", "c", "d", "a"])
        self.assertEqual(list(wrapped.branch(TreePath(2, 1, 0))), [20, 30, 10])
        self.assertEqual(list(wrapped.branch(TreePath(5, 0))), [])
        self.assertEqual(list(unwrapped.branch(TreePath(0, 0))), ["a", "b", "c"])
        self.assertEqual(list(unwrapped.branch(TreePath(2, 1, 0))), [10, 20])

    def test_reverse_list_preserves_paths(self):
        result = ReverseList(self.tree)

        # LIST-only component: one call per branch, paths are kept (Grasshopper does the same)
        self.assertEqual(result.paths, self.tree.paths)
        self.assertEqual(list(result.branch(TreePath(0))), ["d", "c", "b", "a"])
        self.assertEqual(list(result.branch(TreePath(2, 1))), [30, 20, 10])
        self.assertEqual(list(result.branch(TreePath(5))), [])

    def test_partition_list_creates_chunk_sub_branches(self):
        sizes = DataTree.from_branches(
            {
                TreePath(0): [3],
                TreePath(2, 1): [2],
                TreePath(5): [4],
            }
        )

        result = PartitionList(self.tree, sizes)

        self.assertEqual(
            result.paths,
            [
                TreePath(0, 0),
                TreePath(0, 1),
                TreePath(2, 1, 0),
                TreePath(2, 1, 1),
                TreePath(5, 0),
            ],
        )
        self.assertEqual(list(result.branch(TreePath(0, 0))), ["a", "b", "c"])
        self.assertEqual(list(result.branch(TreePath(0, 1))), ["d"])
        self.assertEqual(list(result.branch(TreePath(2, 1, 0))), [10, 20])
        self.assertEqual(list(result.branch(TreePath(2, 1, 1))), [30])
        self.assertEqual(list(result.branch(TreePath(5, 0))), [])


class PerInputAccessMigrationTests(unittest.TestCase):
    """Locks for the components that moved from `__new__`/`_first()` workarounds to declared access."""

    def test_list_item_iterates_indices_per_branch(self):
        result = ListItem(tree(["a", "b", "c", "d"]), tree([0, 2, 4]))
        assert_tree_equal(self, result, {"0": ["a", "c"]})

    def test_list_item_wraps_and_uses_index_tree_as_principal(self):
        wrapped = ListItem(tree(["a", "b", "c"]), tree([4]), True)
        assert_tree_equal(self, wrapped, {"0": ["b"]})
        driven = ListItem(tree(["a", "b", "c"]), tree({"0": [0], "1": [2]}))
        assert_tree_equal(self, driven, {"0": ["a"], "1": ["c"]})

    def test_list_item_out_of_range_without_wrap_keeps_empty_branch(self):
        assert_tree_equal(self, ListItem(tree(["a"]), tree([5])), {"0": []})
        assert_tree_equal(self, ListItem(tree({"0": []}), tree([0])), {"0": []})

    def test_partition_sizes_cycle_with_repeat_last(self):
        result = PartitionList(tree([1, 2, 3, 4, 5, 6, 7]), tree([1, 2]))
        assert_tree_equal(self, result, {"0;0": [1], "0;1": [2, 3], "0;2": [4, 5], "0;3": [6, 7]})

    def test_cull_index_takes_indices_as_list_and_wrap_as_item(self):
        from pyhopper import CullIndex

        result = CullIndex(tree(["a", "b", "c", "d"]), tree([0, 5]), tree([True]))
        assert_tree_equal(self, result, {"0;0": ["c", "d"]})

    def test_shift_list_two_shifts_sub_branch(self):
        result = ShiftList(tree(["a", "b", "c"]), tree([1, 2]), True)
        assert_tree_equal(self, result, {"0;0": ["b", "c", "a"], "0;1": ["c", "a", "b"]})

    def test_sub_list_two_domains_sub_branch(self):
        result = SubList(tree(["a", "b", "c", "d"]), tree([AtomicInterval(0, 1), AtomicInterval(2, 3)]))
        assert_tree_equal(self, result, {"0;0": ["a", "b"], "0;1": ["c", "d"]})
        assert_tree_equal(self, result.index, {"0;0": [0, 1], "0;1": [2, 3]})

    def test_split_list_two_indices_sub_branch(self):
        result = SplitList(tree([1, 2, 3]), tree([1, 2]))
        assert_tree_equal(self, result, {"0;0": [1], "0;1": [1, 2]})
        assert_tree_equal(self, result.list_b, {"0;0": [2, 3], "0;1": [3]})

    def test_interpolate_degree_is_a_scalar_per_branch(self):
        points = tree({"0": [AtomicPoint(0, 0, 0), AtomicPoint(1, 1, 0), AtomicPoint(2, 0, 0), AtomicPoint(3, 1, 0)],
                       "1": [AtomicPoint(0, 0, 1), AtomicPoint(1, 1, 1), AtomicPoint(2, 0, 1), AtomicPoint(3, 1, 1)]})
        result = Interpolate(points, 1)
        self.assertEqual([str(p) for p in result.paths], ["{0}", "{1}"])
        self.assertEqual({curve.degree for curve in result.all_items()}, {1})

    def test_polyline_closed_item_and_nurbs_periodic_item(self):
        square = tree([AtomicPoint(0, 0, 0), AtomicPoint(1, 0, 0), AtomicPoint(1, 1, 0), AtomicPoint(0, 1, 0)])
        closed = Polyline(square, True).all_items()[0]
        self.assertTrue(closed.is_closed)
        periodic = NurbsCurve(square, 2, True).all_items()[0]
        self.assertEqual(len(periodic.control_points), 6)

    def test_merge_positional_and_keyword_keep_paths(self):
        a = tree({"0": [1], "2": [2]})
        b = tree({"0": [3], "5": [4]})
        assert_tree_equal(self, Merge(a, b), {"0": [1, 3], "2": [2], "5": [4]})
        assert_tree_equal(self, Merge(data=[a, b]), Merge(a, b))
        self.assertEqual(Merge().branch_count, 0)  # an explicit empty DataTree result stays empty


if __name__ == "__main__":
    unittest.main()
