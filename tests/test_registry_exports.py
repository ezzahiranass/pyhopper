"""Component registry and lazy top-level exports."""

from __future__ import annotations

import unittest

import pyhopper
from pyhopper.Components.registry import ComponentEntry, component_index, component_key, iter_component_classes, resolve
from pyhopper.Graph.catalog import list_components


class RegistryTests(unittest.TestCase):
    def test_walker_matches_the_catalog(self):
        entries = list(iter_component_classes())
        catalog = list_components()
        self.assertEqual(len(entries), len(catalog))
        self.assertEqual({entry.key for entry in entries}, {item["component_key"] for item in catalog})
        for entry in entries:
            self.assertIsInstance(entry, ComponentEntry)
            self.assertEqual(entry.key, component_key(entry.cls))
            self.assertEqual(entry.cls.__module__.split(".")[2], entry.tab)

    def test_re_exports_are_not_counted_as_components(self):
        keys = {entry.key for entry in iter_component_classes()}
        self.assertNotIn("pyhopper.Components.Curve.Primitive.Cylinder.Cylinder", keys)
        self.assertIn("pyhopper.Components.Surface.Primitive.Cylinder.Cylinder", keys)

    def test_resolve_prefers_non_params_and_reports_ambiguity(self):
        self.assertEqual(resolve("Circle").__module__, "pyhopper.Components.Curve.Primitive.Circle")
        self.assertEqual(resolve("Number").__module__, "pyhopper.Components.Params.Primitive.Number")
        with self.assertRaises(LookupError) as context:
            resolve("Rotate")
        self.assertIn("Transform.Euclidian.Rotate", str(context.exception))
        with self.assertRaises(LookupError):
            resolve("DoesNotExist")

    def test_index_groups_duplicate_names(self):
        index = component_index()
        self.assertGreaterEqual(len(index["Rotate"]), 2)
        self.assertEqual(len(index["ListItem"]), 1)


class LazyExportTests(unittest.TestCase):
    def test_curated_exports_still_win(self):
        self.assertEqual(pyhopper.Rotate.__module__, "pyhopper.Components.Transform.Euclidian.Rotate")
        self.assertEqual(pyhopper.CircleCmp.__module__, "pyhopper.Components.Curve.Primitive.Circle")
        self.assertEqual(pyhopper.CircleParam.__module__, "pyhopper.Components.Params.Geometry.Circle")

    def test_unexported_components_resolve_lazily(self):
        for name in ("Addition", "CircleCNR", "VectorXYZ", "DivideDistance"):
            with self.subTest(name=name):
                component_cls = getattr(pyhopper, name)
                self.assertEqual(component_cls.__name__, name)
        self.assertIn("Addition", dir(pyhopper))

    def test_missing_names_raise_attribute_error(self):
        with self.assertRaises(AttributeError):
            pyhopper.NotAComponent
        with self.assertRaises(AttributeError):
            pyhopper._private


if __name__ == "__main__":
    unittest.main()
