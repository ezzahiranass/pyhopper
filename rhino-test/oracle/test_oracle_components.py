"""Run every oracle case file through pyhopper *and* headless Grasshopper, then compare.

Case files live in ``cases/<Tab>/<Class>.json`` (written by
``scripts/new_component.py``, inputs filled per wave). For each case the same
inputs are fed to the pyhopper component and to the Grasshopper component with
the fixture's ``gh_guid``; the outputs listed in ``compare`` (Grasshopper port
names) are matched to pyhopper outputs by position — the metadata contract
keeps both port lists in Grasshopper order.

Fixture options (all optional):

- ``mode``: ``exact`` (paths and values within ``tolerance``) or ``structural``
  (paths and item counts only);
- ``reparametrize``: input names whose curves are mapped to the [0, 1] domain on
  both sides (pyhopper's Reparametrize port op, Grasshopper's Reparameterize
  flag) so parameter outputs compare;
- ``paths``: ``"exact"`` (default) or ``"simplified"`` — compare simplified
  trees when pyhopper's list-output rule places items differently from
  Grasshopper's ``{path;iteration}``;
- ``nulls``: ``"drop"`` (default) removes Grasshopper nulls before comparing
  (they are the analogue of ``Component.NO_OUTPUT``); ``"keep"`` compares them
  against pyhopper ``None`` items for components that keep index alignment
  (Sift Pattern, Insert Items);
- per case ``"gh": {"skip": "reason"}`` — a documented deviation; the case is
  still exercised in pyhopper but not compared.

Parameter containers (no Grasshopper component params) are skipped.
"""

from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path as FilePath
from typing import Any

from oracle.gh_headless import output_key
from oracle.support import REPO_ROOT, requires_rhino

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.support.components import decode_input, resolve_component, run_component  # noqa: E402
from tests.support.trees import items_close  # noqa: E402

from pyhopper.Core.DataTree import DataTree  # noqa: E402
from pyhopper.Utils.Curves import reparametrize_tree  # noqa: E402

CASES_DIR = FilePath(__file__).resolve().parent / "cases"
DUMP = REPO_ROOT / "rhino-test" / "gh_core_components_r8.json"


def _load_dump() -> dict[str, dict]:
    records = json.loads(DUMP.read_text(encoding="utf-8"))
    return {record["guid"]: record for record in records}


def _describe(tree: DataTree) -> str:
    return "; ".join(f"{path}: {list(branch)!r}" for path, branch in tree.branches()) or "<empty>"


def _places(tolerance: float) -> int:
    return max(0, int(round(-math.log10(tolerance)))) if tolerance > 0 else 12


def compare_trees(testcase: unittest.TestCase, ours: DataTree, theirs: DataTree, *, mode: str, tolerance: float, label: str) -> None:
    testcase.assertEqual([str(p) for p in ours.paths], [str(p) for p in theirs.paths], f"{label}: paths differ\n  pyhopper {_describe(ours)}\n  grasshopper {_describe(theirs)}")
    places = _places(tolerance)
    for path in ours.paths:
        mine, gh = list(ours.branch(path)), list(theirs.branch(path))
        testcase.assertEqual(len(mine), len(gh), f"{label}: item count differs at {path}\n  pyhopper {mine!r}\n  grasshopper {gh!r}")
        if mode == "structural":
            continue
        for index, (a, b) in enumerate(zip(mine, gh)):
            if not items_close(a, b, places):
                testcase.fail(f"{label}: item {index} at {path} differs: pyhopper {a!r} != grasshopper {b!r}")


@requires_rhino
class GrasshopperOracleTests(unittest.TestCase):
    """Populated below with one method per case file."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.dump = _load_dump() if DUMP.exists() else {}


def _make_test(fixture_path: FilePath):
    def test(self: unittest.TestCase) -> None:
        from oracle.gh_headless import solve_component

        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        record = self.dump.get(fixture["gh_guid"])
        if record is None or record.get("inputs") is None:
            self.skipTest("parameter container or unknown Grasshopper component")
        reparametrized = list(fixture.get("reparametrize") or [])
        component_cls = resolve_component(fixture["component"])
        gh_output_names = [port["name"] for port in record["outputs"]]
        pyhopper_output_names = [param.name for param in component_cls.outputs]
        mode = fixture.get("mode", "exact")
        tolerance = float(fixture.get("tolerance", 1e-6))
        simplified = fixture.get("paths") == "simplified"
        drop_nulls = fixture.get("nulls", "drop") != "keep"
        extra = len(getattr(component_cls, "gh_extra_inputs", ()))
        gh_input_names = [param.name for param in component_cls.inputs][: len(component_cls.inputs) - extra]

        for case in fixture["cases"]:
            with self.subTest(case=case["name"]):
                skip = (case.get("gh") or {}).get("skip")
                if skip:
                    self.skipTest(f"documented deviation: {skip}")
                kwargs = {name: decode_input(spec) for name, spec in case.get("inputs", {}).items()}
                for name in reparametrized:
                    if name in kwargs:
                        # the same [0, 1] domain on both sides: pyhopper's Reparametrize port op here,
                        # Grasshopper's Reparameterize flag (a domain reset) in the runner
                        kwargs[name] = reparametrize_tree(DataTree.coerce(kwargs[name]))
                ours = run_component(component_cls, settings=case.get("settings") or None, **kwargs)
                gh_inputs: dict[int, DataTree] = {}
                for name, value in kwargs.items():
                    self.assertIn(name, gh_input_names, f"{name} is not a Grasshopper-mapped input")
                    index = gh_input_names.index(name)
                    if isinstance(value, list):
                        # variadic streams occupy Grasshopper's numbered ports from the variadic index on
                        if index + len(value) > len(record["inputs"]):
                            self.skipTest(f"{name}: {len(value)} streams exceed the {len(record['inputs']) - index} Grasshopper ports")
                        for offset, stream in enumerate(value):
                            gh_inputs[index + offset] = DataTree.coerce(stream)
                    else:
                        gh_inputs[index] = DataTree.coerce(value)
                reparametrize_indices = tuple(gh_input_names.index(name) for name in reparametrized if name in gh_input_names)
                theirs, messages = solve_component(fixture["gh_guid"], gh_inputs, drop_nulls=drop_nulls, reparametrize=reparametrize_indices)
                compare = case.get("compare") or [output_key(gh_output_names, index) for index in range(len(gh_output_names))]
                for gh_name in compare:
                    keys = [output_key(gh_output_names, index) for index in range(len(gh_output_names))]
                    self.assertIn(gh_name, keys, f"{gh_name} is not an output of {record['name']} ({keys})")
                    position = keys.index(gh_name)
                    our_name = pyhopper_output_names[position]
                    mine, gh = ours[our_name], theirs[gh_name]
                    if simplified:
                        mine, gh = mine.simplify(), gh.simplify()
                    compare_trees(self, mine, gh, mode=mode, tolerance=tolerance, label=f"{case['name']}.{our_name} (GH messages: {messages})")

    test.__doc__ = f"oracle case file {fixture_path.relative_to(CASES_DIR).as_posix()}"
    return test


for _fixture in sorted(CASES_DIR.rglob("*.json")) if CASES_DIR.exists() else []:
    _name = "test_" + "_".join(_fixture.relative_to(CASES_DIR).with_suffix("").parts)
    setattr(GrasshopperOracleTests, _name, _make_test(_fixture))


if __name__ == "__main__":
    unittest.main()
