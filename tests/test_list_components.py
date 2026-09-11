"""List component behaviour locks (ported from pyhopper-web/api; extended by the per-input access work)."""
from __future__ import annotations

import unittest


from pyhopper import (
    AtomicInterval,
    ListLength,
    PartitionList,
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

        self.assertEqual(result.paths, self.tree.paths)
        self.assertEqual(list(result.branch(TreePath(0))), ["a", "b"])
        self.assertEqual(list(result.list_b.branch(TreePath(0))), ["c", "d"])
        self.assertEqual(list(result.branch(TreePath(2, 1))), [10])
        self.assertEqual(list(result.list_b.branch(TreePath(2, 1))), [20, 30])
        self.assertEqual(list(result.branch(TreePath(5))), [])
        self.assertEqual(list(result.list_b.branch(TreePath(5))), [])

    def test_sub_list_preserves_paths_and_reports_indices(self):
        domains = DataTree.from_branches(
            {
                TreePath(0): [AtomicInterval(1, 2)],
                TreePath(2, 1): [AtomicInterval(2, 0)],
                TreePath(5): [AtomicInterval(0, 1)],
            }
        )

        result = SubList(self.tree, domains, False)

        self.assertEqual(result.paths, self.tree.paths)
        self.assertEqual(list(result.branch(TreePath(0))), ["b", "c"])
        self.assertEqual(list(result.index.branch(TreePath(0))), [1, 2])
        self.assertEqual(list(result.branch(TreePath(2, 1))), [30, 20, 10])
        self.assertEqual(list(result.index.branch(TreePath(2, 1))), [2, 1, 0])
        self.assertEqual(list(result.branch(TreePath(5))), [])
        self.assertEqual(list(result.index.branch(TreePath(5))), [])

    def test_sub_list_wraps_indices_per_branch(self):
        tree = DataTree.from_branches({TreePath(4, 2): ["a", "b", "c"]})

        result = SubList(tree, AtomicInterval(-1, 4), True)

        self.assertEqual(result.paths, [TreePath(4, 2)])
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

        self.assertEqual(list(wrapped.branch(TreePath(0))), ["b", "c", "d", "a"])
        self.assertEqual(list(wrapped.branch(TreePath(2, 1))), [20, 30, 10])
        self.assertEqual(list(wrapped.branch(TreePath(5))), [])
        self.assertEqual(list(unwrapped.branch(TreePath(0))), ["a", "b", "c"])
        self.assertEqual(list(unwrapped.branch(TreePath(2, 1))), [10, 20])

    def test_reverse_list_preserves_paths(self):
        result = ReverseList(self.tree)

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


if __name__ == "__main__":
    unittest.main()
