"""The base-class placement rules, checked against Grasshopper itself.

These lock the behaviour ``Component`` implements for every component, using
real Grasshopper components as the oracle:

- a component with an ITEM input writes list outputs to ``{path;iteration}``
  (Series with one start at ``{0}`` -> ``{0;0}``; at ``{2;1}`` -> ``{2;1;0}``);
- a component whose inputs are all LIST/TREE access writes lists into
  ``{path}`` (Mass Addition partial results);
- an empty input branch leaves the list path behind, empty (``{0;0}: []``);
- item outputs stay at ``{path}`` (Mass Addition result, List Item).
"""

from __future__ import annotations

import sys
import unittest

from oracle.support import REPO_ROOT, requires_rhino

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.support.trees import assert_tree_equal, tree  # noqa: E402

SERIES = "e64c5fb1-845c-4ab1-8911-5f338516ba67"
MASS_ADDITION = "5b850221-b527-4bd6-8c62-e94168cd6efa"
LIST_ITEM = "59daf374-bc21-4a5e-8282-5504fb7ae9ae"


def _paths(data_tree) -> list[str]:
    return [str(path) for path in data_tree.paths]


@requires_rhino
class SolveRuleOracleTests(unittest.TestCase):
    def _gh(self, guid, inputs):
        from oracle.gh_headless import solve_component

        outputs, _ = solve_component(guid, inputs)
        return outputs

    def test_item_iterating_component_places_lists_one_level_down(self) -> None:
        from pyhopper import Series

        for start in (tree([0.0]), tree({"2;1": [0.0]}), tree({"0": [0.0, 10.0]}), tree({"0": [0.0], "1": [10.0]})):
            with self.subTest(start=_paths(start)):
                theirs = self._gh(SERIES, {0: start, 1: tree([1.0]), 2: tree([3])})["Series"]
                ours = Series(start, 1.0, 3)
                assert_tree_equal(self, ours, theirs)

    def test_list_only_component_keeps_the_branch_path(self) -> None:
        from pyhopper import MassAddition

        data = tree({"0": [1.0, 2.0], "3;2": [10.0, 20.0, 30.0]})
        theirs = self._gh(MASS_ADDITION, {0: data})
        ours = MassAddition(data)
        assert_tree_equal(self, ours.output("result"), theirs["Result"])
        assert_tree_equal(self, ours.output("partial_results"), theirs["Partial Results"])
        self.assertEqual(_paths(theirs["Partial Results"]), ["{0}", "{3;2}"])

    def test_empty_branch_leaves_the_list_path_behind(self) -> None:
        from pyhopper import Series

        start = tree({"0": [], "1": [5.0]})
        theirs = self._gh(SERIES, {0: start, 1: tree([1.0]), 2: tree([3])})["Series"]
        self.assertEqual(_paths(theirs), ["{0;0}", "{1;0}"])
        assert_tree_equal(self, Series(start, 1.0, 3), theirs)

    def test_item_output_stays_on_the_branch_and_nulls_read_as_nothing(self) -> None:
        from pyhopper import ListItem

        items = tree({"0": ["a", "b"], "1": ["c"]})
        theirs = self._gh(LIST_ITEM, {0: items, 1: tree([0, 7]), 2: tree([False])})["Item"]
        # Grasshopper emits a null for the out-of-range index; the runner drops nulls, pyhopper emits nothing
        self.assertEqual(_paths(theirs), ["{0}", "{1}"])
        assert_tree_equal(self, ListItem(items, tree([0, 7]), False), theirs)


if __name__ == "__main__":
    unittest.main()
