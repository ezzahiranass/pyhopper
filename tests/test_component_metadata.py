"""Grasshopper metadata contract: components that declare a gh_guid must match the GH dump.

For every component with ``gh_guid``: display_name / nickname equal the Grasshopper
record, the module path matches the Grasshopper tab and subcategory, and the declared
inputs are the Grasshopper inputs (mapped through ``Graph/naming.py``) followed by any
pyhopper-only ``gh_extra_inputs``. The variadic last input absorbs Grasshopper's
numbered stream ports.
"""

from __future__ import annotations

import json
import unittest
from importlib import import_module
from pathlib import Path

from pyhopper.Graph.catalog import list_components
from pyhopper.Graph.naming import class_name_for, port_name_for, variadic_port_name

DUMP = Path(__file__).resolve().parents[1] / "rhino-test" / "gh_core_components_r8.json"
SUBCATEGORY_ALIASES = {"Euclidean": "Euclidian"}  # the folder keeps its historical spelling
GH_ACCESS_TO_PYHOPPER = {"item": "item", "list": "list", "tree": "tree"}


def _load_dump() -> dict[str, dict]:
    records = json.loads(DUMP.read_text(encoding="utf-8"))
    return {record["guid"]: record for record in records}


def _resolve(component_key: str):
    module_name, _, class_name = component_key.rpartition(".")
    return getattr(import_module(module_name), class_name)


def _expected_inputs(record: dict) -> list[tuple[str, str]]:
    """(name, access) pairs after variadic collapse, in Grasshopper order."""
    expected: list[tuple[str, str]] = []
    for port in record["inputs"] or []:
        name = port_name_for(port["name"], record["name"])
        access = GH_ACCESS_TO_PYHOPPER[port["access"]]
        if variadic_port_name(port["name"]) and expected and expected[-1][0] == name:
            continue  # "Stream 1" collapses into the same variadic port as "Stream 0"
        expected.append((name, access))
    return expected


@unittest.skipUnless(DUMP.exists(), "Grasshopper dump not available")
class ComponentMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dump = _load_dump()
        cls.entries = [entry for entry in list_components() if entry.get("gh_guid")]

    def test_some_components_declare_metadata(self) -> None:
        self.assertGreater(len(self.entries), 0)

    def test_guid_exists_in_dump_and_names_match(self) -> None:
        for entry in self.entries:
            with self.subTest(component=entry["component_key"]):
                record = self.dump.get(entry["gh_guid"])
                self.assertIsNotNone(record, f"gh_guid {entry['gh_guid']} is not in the Grasshopper dump")
                self.assertEqual(entry["display_name"], record["name"])
                self.assertEqual(entry["nickname"], record["nickname"])

    def test_location_matches_grasshopper_tab_and_subcategory(self) -> None:
        for entry in self.entries:
            record = self.dump[entry["gh_guid"]]
            with self.subTest(component=entry["component_key"]):
                self.assertEqual(entry["tab"], record["category"])
                expected_category = SUBCATEGORY_ALIASES.get(record["subcategory"], record["subcategory"])
                self.assertEqual(entry["category"], expected_category)

    def test_class_name_is_derived_from_the_grasshopper_name(self) -> None:
        for entry in self.entries:
            record = self.dump[entry["gh_guid"]]
            with self.subTest(component=entry["component_key"]):
                self.assertEqual(entry["component"], class_name_for(record["name"], record["category"], record["subcategory"]))

    def test_inputs_follow_the_grasshopper_port_contract(self) -> None:
        for entry in self.entries:
            record = self.dump[entry["gh_guid"]]
            if record["inputs"] is None:
                continue  # parameter containers have no component params in the dump
            component_cls = _resolve(entry["component_key"])
            with self.subTest(component=entry["component_key"]):
                declared = [(param.name, param.access.value) for param in component_cls.inputs]
                extra = tuple(getattr(component_cls, "gh_extra_inputs", ()))
                if extra:
                    self.assertEqual(tuple(name for name, _ in declared[-len(extra):]), extra, "gh_extra_inputs must be the trailing inputs")
                    declared = declared[: len(declared) - len(extra)]
                self.assertEqual(declared, _expected_inputs(record))


if __name__ == "__main__":
    unittest.main()
