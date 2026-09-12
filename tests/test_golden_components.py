"""Run every golden component fixture under tests/golden/components/.

Each JSON file describes one component (its dotted class path) and a list
of cases: inputs, optional settings, and either expected output trees, an
expected exception, or ``shape_only`` branch counts. One test method is
generated per fixture so failures point at the component.

Regenerate expectations from the current code with
``PYHOPPER_UPDATE_GOLDEN=1`` (cases keep their inputs; ``expect`` is rewritten).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.support.components import ComponentCase, decode_input, resolve_component, run_case, run_component
from tests.support.golden import UPDATE, golden_path, load_json, save_json
from tests.support.trees import tree_to_spec

COMPONENT_GOLDENS = golden_path("components")


def _case_from_json(data: dict) -> ComponentCase:
    return ComponentCase(
        name=data["name"],
        inputs=data.get("inputs", {}),
        expected=data.get("expect", {}),
        settings=data.get("settings") or None,
        raises=data.get("raises"),
        shape_only=bool(data.get("shape_only", False)),
        places=int(data.get("places", 7)),
    )


def _record_expectations(component_cls, fixture: dict) -> None:
    for case in fixture["cases"]:
        if case.get("raises") or case.get("shape_only"):
            continue
        kwargs = {name: decode_input(spec) for name, spec in case.get("inputs", {}).items()}
        outputs = run_component(component_cls, settings=case.get("settings") or None, **kwargs)
        wanted = case.get("expect") or {name: None for name in outputs}
        case["expect"] = {name: tree_to_spec(outputs[name]) for name in wanted if name in outputs}


def _make_test(fixture_path: Path):
    def test(self: unittest.TestCase) -> None:
        fixture = load_json(fixture_path)
        component_cls = resolve_component(fixture["component"])
        if UPDATE:
            _record_expectations(component_cls, fixture)
            save_json(fixture_path, fixture)
        self.assertTrue(fixture.get("cases"), f"{fixture_path.name}: fixture has no cases")
        for raw_case in fixture["cases"]:
            case = _case_from_json(raw_case)
            with self.subTest(case=case.name):
                run_case(self, component_cls, case)

    test.__doc__ = f"golden fixture {fixture_path.relative_to(COMPONENT_GOLDENS).as_posix()}"
    return test


class GoldenComponentTests(unittest.TestCase):
    """Populated below with one method per fixture file."""


for _fixture in sorted(COMPONENT_GOLDENS.rglob("*.json")) if COMPONENT_GOLDENS.exists() else []:
    _name = "test_" + "_".join(_fixture.relative_to(COMPONENT_GOLDENS).with_suffix("").parts)
    setattr(GoldenComponentTests, _name, _make_test(_fixture))


if __name__ == "__main__":
    unittest.main()
