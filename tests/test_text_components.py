from __future__ import annotations

import unittest

from pyhopper import Characters, Concatenate, ReplaceText, TextCase, TextLength, TextSplit
from pyhopper.Core.DataTree import DataTree
from pyhopper.Core.Path import Path as TreePath


class TextComponentTests(unittest.TestCase):
    def test_text_case_outputs_upper_and_lower_text(self):
        result = TextCase("PyHopper")
        self.assertEqual(result.upper_case.all_items(), ["PYHOPPER"])
        self.assertEqual(result.lower_case.all_items(), ["pyhopper"])

    def test_text_case_supports_turkish_casing(self):
        result = TextCase("Istanbul izmir", "tr-TR")
        self.assertEqual(result.upper_case.all_items(), ["ISTANBUL \u0130ZM\u0130R"])
        self.assertEqual(result.lower_case.all_items(), ["\u0131stanbul izmir"])

    def test_concatenate_matches_items_and_preserves_paths(self):
        left = DataTree.from_branches({TreePath(2): ["a", "b"]})
        result = Concatenate(left, "!")
        self.assertEqual(result.paths, [TreePath(2)])
        self.assertEqual(result.all_items(), ["a!", "b!"])

    def test_text_split_uses_each_separator_character(self):
        result = TextSplit("one,two;three", ",;")
        self.assertEqual(result.all_items(), ["one", "two", "three"])

    def test_text_length_counts_unicode_characters(self):
        self.assertEqual(TextLength("h\u00e9llo").all_items(), [5])

    def test_characters_outputs_characters_and_unicode_values(self):
        result = Characters("hello")
        self.assertEqual(result.result.all_items(), ["h", "e", "l", "l", "o"])
        self.assertEqual(result.unicode.all_items(), [104, 101, 108, 108, 111])

    def test_replace_text_replaces_or_removes_all_occurrences(self):
        self.assertEqual(ReplaceText("one two one", "one", "1").all_items(), ["1 two 1"])
        self.assertEqual(ReplaceText("one two one", "one").all_items(), [" two "])


if __name__ == "__main__":
    unittest.main()
