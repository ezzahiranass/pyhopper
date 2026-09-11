"""Wave A2 helpers: item identity, Grasshopper text formatting, list patterns, Jitter properties."""

from __future__ import annotations

import unittest

from tests.support.trees import assert_tree_equal, tree

from pyhopper.Components.Sets._lists import cycle, pad_to, resolve_index
from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.TypeSystem import coerce_item
from pyhopper.Utils.Items import index_of, indices_of, item_key
from pyhopper.Utils.Text import format_number, format_value


class ItemKeyTests(unittest.TestCase):
    def test_type_sensitive_like_grasshopper(self):
        # 1, 1.0, True and "1" are four different set members in Grasshopper
        keys = {item_key(value) for value in (1, 1.0, True, "1")}
        self.assertEqual(len(keys), 4)

    def test_atoms_compare_by_value(self):
        self.assertEqual(item_key(AtomicPoint(1, 2, 3)), item_key(AtomicPoint(1.0, 2.0, 3.0)))
        self.assertNotEqual(item_key(AtomicPoint(1, 2, 3)), item_key(AtomicPoint(1, 2, 4)))

    def test_index_helpers(self):
        items = ["a", 2, 2.0, "a"]
        self.assertEqual(index_of(items, "a"), 0)
        self.assertEqual(index_of(items, 2.0), 2)
        self.assertEqual(index_of(items, "z"), -1)
        self.assertEqual(indices_of(items, "a"), [0, 3])


class TextFormattingTests(unittest.TestCase):
    def test_numbers_format_like_dotnet(self):
        table = {
            1.0: "1",
            2.5: "2.5",
            -0.5: "-0.5",
            1e-7: "1E-07",
            123456789.0: "123456789",
            0.1 + 0.2: "0.30000000000000004",
            0.0001: "0.0001",
            0.00001: "1E-05",
            1e15: "1E+15",
            1234567890123456.0: "1.234567890123456E+15",
            1e16: "1E+16",
            1.5e20: "1.5E+20",
            -2.5e-10: "-2.5E-10",
            100.0: "100",
        }
        for value, expected in table.items():
            with self.subTest(value=value):
                self.assertEqual(format_number(value), expected)
        self.assertEqual(format_number(3), "3")
        self.assertEqual(format_number(True), "True")

    def test_format_value_passes_text_through(self):
        self.assertEqual(format_value("hi"), "hi")
        self.assertEqual(format_value(False), "False")

    def test_str_ports_accept_numbers_and_booleans(self):
        self.assertEqual(coerce_item(2.0, str), "2")
        self.assertEqual(coerce_item(True, str), "True")
        self.assertEqual(coerce_item("x", str), "x")


class ListHelperTests(unittest.TestCase):
    def test_cycle(self):
        self.assertEqual(cycle([True, False], 5), [True, False, True, False, True])
        self.assertEqual(cycle([], 3), [])
        self.assertEqual(cycle([1], 0), [])

    def test_resolve_index(self):
        self.assertEqual(resolve_index(4, 3, True, "X"), 1)
        self.assertEqual(resolve_index(-1, 3, True, "X"), 2)
        self.assertEqual(resolve_index(2, 3, False, "X"), 2)
        with self.assertRaises(IndexError):
            resolve_index(3, 3, False, "X")
        with self.assertRaises(IndexError):
            resolve_index(0, 0, True, "X")

    def test_pad_to(self):
        self.assertEqual(pad_to(["a"], 3), ["a", None, None])
        self.assertEqual(pad_to(["a", "b"], 1), ["a", "b"])


class JitterPropertyTests(unittest.TestCase):
    def test_seeded_shuffle_is_a_deterministic_permutation(self):
        from pyhopper.Components.Sets.Sequence.Jitter import Jitter

        items = list("abcdefgh")
        first = Jitter(tree(items), 1.0, 3)
        second = Jitter(tree(items), 1.0, 3)
        assert_tree_equal(self, first.output("values"), second.output("values"))
        assert_tree_equal(self, first.output("indices"), second.output("indices"))
        values = first.output("values").all_items()
        indices = first.output("indices").all_items()
        self.assertEqual(sorted(values), items)
        self.assertEqual(sorted(indices), list(range(len(items))))
        self.assertEqual([items[index] for index in indices], values)
        self.assertNotEqual(values, items, "a full jitter of eight items should move something")
        other = Jitter(tree(items), 1.0, 4).output("values").all_items()
        self.assertNotEqual(other, values, "different seeds should give different sequences")


if __name__ == "__main__":
    unittest.main()
