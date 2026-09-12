"""scripts/new_component.py generates importable, catalog-compatible component skeletons."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import new_component  # noqa: E402

from pyhopper.Core.Component import Component  # noqa: E402

DUMP = REPO_ROOT / "rhino-test" / "gh_core_components_r8.json"


def _quiet(argv: list[str]) -> int:
    with contextlib.redirect_stdout(io.StringIO()):
        return new_component.main(argv)


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(DUMP.exists(), "Grasshopper dump not available")
class ScaffoldTests(unittest.TestCase):
    def _scaffold(self, name: str, *extra: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        argv = [name, "--out", str(root / "Components"), "--golden", str(root / "golden"), "--oracle", str(root / "oracle"), *extra]
        self.assertEqual(_quiet(argv), 0)
        return root

    def test_variadic_component_scaffold_imports_and_matches_metadata(self):
        root = self._scaffold("Sort List")
        module_path = root / "Components" / "Sets" / "List" / "SortList.py"
        self.assertTrue(module_path.exists())
        module = _load_module(module_path)
        cls = module.SortList
        self.assertTrue(issubclass(cls, Component))
        self.assertEqual((cls.display_name, cls.nickname), ("Sort List", "Sort"))
        self.assertEqual([p.name for p in cls.inputs], ["keys", "values"])
        self.assertTrue(cls.variadic_inputs)
        self.assertEqual([o.name for o in cls.outputs], ["keys", "values"])
        with self.assertRaises(NotImplementedError):
            cls([3.0, 1.0])
        golden = json.loads((root / "golden" / "Sets" / "SortList.json").read_text(encoding="utf-8"))
        self.assertEqual(golden["component"], "pyhopper.Components.Sets.List.SortList.SortList")
        self.assertEqual(len(golden["cases"]), 3)
        self.assertTrue((root / "oracle" / "Sets" / "SortList.json").exists())
        self.assertTrue((root / "Components" / "Sets" / "__init__.py").exists())

    def test_symbol_names_and_duplicate_outputs_are_mapped(self):
        root = self._scaffold("Line | Line")
        module = _load_module(root / "Components" / "Intersect" / "Mathematical" / "LineLine.py")
        self.assertEqual([p.name for p in module.LineLine.inputs], ["line_1", "line_2"])
        self.assertEqual([o.name for o in module.LineLine.outputs], ["param_a", "param_b", "point_a", "point_b"])
        root = self._scaffold("Length Parameter")
        module = _load_module(root / "Components" / "Curve" / "Analysis" / "LengthParameter.py")
        self.assertEqual([o.name for o in module.LengthParameter.outputs], ["length_before", "length_after"])

    def test_euclidean_maps_to_the_existing_folder_and_ambiguity_is_reported(self):
        root = self._scaffold("Rotate 3D")
        self.assertTrue((root / "Components" / "Transform" / "Euclidian" / "Rotate3D.py").exists())
        with self.assertRaises(SystemExit):
            _quiet(["Circle", "--dry-run"])  # exists in Params and Curve

    def test_existing_files_are_not_overwritten_without_force(self):
        root = self._scaffold("Remap Numbers")
        target = root / "Components" / "Maths" / "Domain" / "RemapNumbers.py"
        target.write_text("# custom\n", encoding="utf-8")
        argv = ["Remap Numbers", "--out", str(root / "Components"), "--golden", str(root / "golden"), "--oracle", str(root / "oracle")]
        new_component.main(argv)
        self.assertEqual(target.read_text(encoding="utf-8"), "# custom\n")
        new_component.main(argv + ["--force"])
        self.assertIn("class RemapNumbers(Component)", target.read_text(encoding="utf-8"))

    def test_check_names_passes_on_the_repository(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(new_component.check_names(REPO_ROOT / "pyhopper" / "Components"), 0)


if __name__ == "__main__":
    unittest.main()
