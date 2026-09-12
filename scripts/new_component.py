"""Scaffold a pyhopper component from its Grasshopper definition.

Usage:
    python scripts/new_component.py "Remap Numbers"
    python scripts/new_component.py "Circle" --tab Curve --sub Primitive
    python scripts/new_component.py "Line | Line" --dry-run
    python scripts/new_component.py --check-names

The Grasshopper record (name, nickname, GUID, ports with access) comes from
``rhino-test/gh_core_components_r8.json`` — never from memory. Class and port
names are derived by ``pyhopper/Graph/naming.py`` so they match what the
metadata and naming tests expect. The generated module compiles and shows up
in the catalog immediately; ``generate()`` raises ``NotImplementedError`` until
you fill it in. A golden fixture stub and an oracle case stub are written too.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from pyhopper.Graph.naming import GH_TYPE_HINTS, class_name_for, port_name_for, variadic_port_name  # noqa: E402

SUBCATEGORY_FOLDERS = {"Euclidean": "Euclidian"}  # the folder keeps its historical spelling
ATOM_HINTS = {
    "AtomicPoint", "AtomicVector", "AtomicPlane", "AtomicLine", "AtomicCircle", "AtomicArc",
    "AtomicRectangle", "AtomicBox", "AtomicMesh", "AtomicTransform", "AtomicBrep", "AtomicInterval",
    "AtomicInterval2",
}
TYPESPEC_HINTS = {"CURVE", "SURFACE", "GEOMETRY"}
# Default expressions for ports Grasshopper does not mark optional. Geometry stays required.
DEFAULTS = {
    "float": "0.0",
    "int": "0",
    "bool": "False",
    "str": '""',
    "AtomicPlane": "AtomicPlane.world_xy()",
    "AtomicVector": "AtomicVector.unit_z()",
    "AtomicPoint": "AtomicPoint.origin()",
    "AtomicInterval": "AtomicInterval(0.0, 1.0)",
    "AtomicInterval2": "AtomicInterval2()",
    "Path": "Path(0)",
}
CHECKLIST = """
Next steps
  1. Implement generate() - math belongs in pyhopper/Utils/* or a sibling _helpers.py.
  2. Fix defaults/optional flags where Grasshopper's behaviour differs from the scaffold guess.
  3. Fill the golden fixture: {golden} (>= 3 cases: typical, multi-branch, edge/raise).
  4. Fill the oracle case: {oracle} (mode exact / structural / invariants).
  5. Run:  .venv\\Scripts\\python -m unittest discover -s tests -t . -k {cls} -v
           .venv\\Scripts\\python -m unittest discover -s tests -t . -k catalog -k metadata -k naming
  6. Record every Grasshopper deviation in the class docstring `Notes:` section.
  7. Check Grasshopper's persistent defaults with rhino-test\.venv\Scripts\python rhino-test\gh_defaults.py "<GH name>"
     and probe unclear behaviour with rhino-test\gh_probe.py before deciding semantics.
"""


def load_records(dump: Path) -> list[dict]:
    return json.loads(dump.read_text(encoding="utf-8"))


def find_record(records: list[dict], name: str, tab: str | None, sub: str | None, guid: str | None = None) -> dict:
    matches = [r for r in records if r["name"] == name]
    if guid:
        matches = [r for r in matches if r["guid"].lower().startswith(guid.lower())]
    if tab:
        matches = [r for r in matches if r["category"] == tab]
    if sub:
        matches = [r for r in matches if r["subcategory"] == sub]
    if not matches:
        raise SystemExit(f"No Grasshopper component named {name!r}" + (f" in {tab}/{sub}" if tab or sub else ""))
    if len(matches) > 1:
        options = ", ".join(f"--tab {r['category']} --sub {r['subcategory']} --guid {r['guid'][:8]} ({r['nickname']})" for r in matches)
        raise SystemExit(f"{name!r} is ambiguous; pass one of: {options}")
    return matches[0]


def hint_for(gh_type: str) -> str:
    return GH_TYPE_HINTS.get(gh_type, "None")


def build_inputs(record: dict) -> tuple[list[dict], bool]:
    """Port dicts (name, hint, access, optional, default, gh) with variadic streams collapsed."""
    ports: list[dict] = []
    variadic = False
    for port in record["inputs"] or []:
        name = port_name_for(port["name"], record["name"])
        if variadic_port_name(port["name"]):
            if ports and ports[-1]["name"] == name:
                ports[-1]["gh"].append(port["name"])
                continue
            variadic = True
        hint = hint_for(port["type"])
        optional = bool(port["optional"])
        # scalar type defaults only make sense for item ports; list/tree ports stay required
        # (fill in Grasshopper's persistent default by hand: rhino-test/gh_defaults.py prints it)
        default = None if optional or port["access"] != "item" else DEFAULTS.get(hint)
        ports.append({
            "name": name,
            "hint": hint,
            "access": port["access"].upper(),
            "optional": optional,
            "default": default,
            "description": port["description"],
            "gh": [port["name"]],
            "nick": port["nickname"],
        })
    return ports, variadic


def build_outputs(record: dict) -> list[dict]:
    seen: Counter = Counter()
    outputs: list[dict] = []
    for port in record["outputs"] or []:
        duplicate = seen[port["name"]] > 0
        seen[port["name"]] += 1
        name = port_name_for(port["name"], record["name"], duplicate=duplicate, output=True)
        if any(existing["name"] == name for existing in outputs):
            name = f"{name}_{seen[port['name']]}"
        outputs.append({
            "name": name,
            "hint": hint_for(port["type"]),
            "access": port["access"].upper(),
            "description": port["description"],
            "gh": port["name"],
            "nick": port["nickname"],
        })
    return outputs


def render_module(record: dict, class_name: str, inputs: list[dict], outputs: list[dict], variadic: bool) -> str:
    hints_used = {p["hint"] for p in inputs} | {o["hint"] for o in outputs}
    atom_imports = sorted(h for h in hints_used if h in ATOM_HINTS)
    for port in inputs:
        if port["default"] and port["default"].split("(")[0].split(".")[0] in ATOM_HINTS:
            atom_imports.append(port["default"].split("(")[0].split(".")[0])
    atom_imports = sorted(set(atom_imports))
    spec_imports = sorted(h for h in hints_used if h in TYPESPEC_HINTS)

    lines = [f'"""{class_name} - {record["description"].rstrip(".")} (Grasshopper "{record["name"]}")."""', "", "from __future__ import annotations", ""]
    if atom_imports:
        lines.append(f"from pyhopper.Core.Atoms import {', '.join(atom_imports)}")
    lines.append("from pyhopper.Core.Component import Access, Component, InputParam, OutputParam")
    if "Path" in hints_used:
        lines.append("from pyhopper.Core.Path import Path")
    if spec_imports:
        lines.append(f"from pyhopper.Core.TypeSystem import {', '.join(spec_imports)}")
    lines += ["", "", f"class {class_name}(Component):", f'    """{record["description"].rstrip(".")}.', ""]
    if inputs:
        lines.append("    Inputs:")
        for port in inputs:
            gh = " / ".join(port["gh"])
            lines.append(f"        {port['name']}: {port['description']} (Grasshopper {gh} [{port['access'].lower()}]).")
        lines.append("")
    if outputs:
        lines.append("    Outputs:")
        for port in outputs:
            lines.append(f"        {port['name']}: {port['description']} (Grasshopper {port['gh']}).")
        lines.append("")
    lines += [
        "    Notes:",
        f"        Grasshopper: {record['category']} > {record['subcategory']} > {record['name']} ({record['nickname']}).",
        "        pyhopper decisions: TODO — record every deviation from Grasshopper here.",
        '    """',
        "",
        f'    display_name = "{record["name"]}"',
        f'    nickname = "{record["nickname"]}"',
        f'    gh_guid = "{record["guid"]}"',
        "",
    ]
    if inputs:
        lines.append("    inputs = [")
        for port in inputs:
            args = [f'"{port["name"]}"', port["hint"], f"Access.{port['access']}"]
            if port["optional"]:
                args.append("optional=True")
            elif port["default"] is not None:
                args.append(f"default={port['default']}")
            lines.append(f"        InputParam({', '.join(args)}),")
        lines.append("    ]")
    else:
        lines.append("    inputs = []")
    lines.append("    outputs = [")
    for port in outputs:
        args = [f'"{port["name"]}"']
        if port["hint"] != "None":
            args.append(port["hint"])
        if port["access"] != "ITEM":
            args.append(f"access=Access.{port['access']}")
        lines.append(f"        OutputParam({', '.join(args)}),")
    lines.append("    ]")
    if variadic:
        lines.append("    variadic_inputs = True")
    lines.append("")
    signature = ", ".join(
        f"{p['name']}={'None' if p['optional'] or p['default'] is None else p['default']}" for p in inputs
    )
    lines.append(f"    def generate(self{', ' + signature if signature else ''}):")
    lines.append(f'        raise NotImplementedError("TODO: implement {class_name}.generate() per the Notes section")')
    lines.append("")
    return "\n".join(lines)


def _oracle_output_keys(record: dict) -> list[str]:
    """Grasshopper output names with ``#2`` suffixes for repeats (mirrors oracle.gh_headless.output_key)."""
    names = [o["name"] for o in (record["outputs"] or [])]
    keys = []
    for index, name in enumerate(names):
        repeat = names[:index].count(name)
        keys.append(name if repeat == 0 else f"{name}#{repeat + 1}")
    return keys


def render_golden(record: dict, class_key: str, outputs: list[dict]) -> str:
    fixture = {
        "component": class_key,
        "gh_guid": record["guid"],
        "tolerance": 1e-9,
        "oracle": {"mode": "exact", "reparametrize": []},
        "cases": [
            {"name": "typical", "inputs": {}, "expect": {o["name"]: {} for o in outputs}},
            {"name": "multi_branch", "inputs": {}, "expect": {o["name"]: {} for o in outputs}},
            {"name": "edge_or_raise", "inputs": {}, "raises": "ValueError"},
        ],
    }
    return json.dumps(fixture, indent=1, ensure_ascii=False) + "\n"


def render_oracle(record: dict, class_key: str) -> str:
    case = {
        "component": class_key,
        "gh_guid": record["guid"],
        "mode": "exact",
        "tolerance": 1e-6,
        "reparametrize": [],
        "cases": [{"name": "typical", "inputs": {}, "compare": _oracle_output_keys(record)}],
    }
    return json.dumps(case, indent=1, ensure_ascii=False) + "\n"


def _display(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def write(path: Path, text: str, force: bool, dry_run: bool) -> None:
    if path.exists() and not force:
        print(f"  skip (exists)  {_display(path)}")
        return
    if dry_run:
        print(f"  would write    {_display(path)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  wrote          {_display(path)}")


def check_names(out_root: Path) -> int:
    """Report class names that disagree with naming.py or collide outside Params."""
    from pyhopper.Components.registry import iter_component_classes

    problems = 0
    names: Counter = Counter()
    for entry in iter_component_classes():
        names[(entry.tab == "Params", entry.name)] += 1
        guid = getattr(entry.cls, "gh_guid", None)
        display = getattr(entry.cls, "display_name", None)
        if guid and display:
            expected = class_name_for(display, entry.tab, {"Euclidian": "Euclidean"}.get(entry.category, entry.category), guid)
            if expected != entry.name:
                problems += 1
                print(f"  name mismatch  {entry.key}: expected {expected!r} from {display!r}")
    for (is_params, name), count in names.items():
        if count > 1 and not is_params and name not in {"Rotate", "Circle", "Line", "Cylinder"}:
            problems += 1
            print(f"  duplicate      {name!r} appears {count} times outside Params")
    print("check-names:", "ok" if problems == 0 else f"{problems} problem(s)")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", nargs="?", help="Grasshopper component name, e.g. \"Remap Numbers\"")
    parser.add_argument("--tab", help="Grasshopper tab, to disambiguate")
    parser.add_argument("--sub", help="Grasshopper subcategory, to disambiguate")
    parser.add_argument("--dump", type=Path, default=REPO_ROOT / "rhino-test" / "gh_core_components_r8.json")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "pyhopper" / "Components")
    parser.add_argument("--golden", type=Path, default=REPO_ROOT / "tests" / "golden" / "components")
    parser.add_argument("--oracle", type=Path, default=REPO_ROOT / "rhino-test" / "oracle" / "cases")
    parser.add_argument("--guid", help="GUID (or prefix) when Grasshopper ships two components under one name")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    parser.add_argument("--dry-run", action="store_true", help="print what would be written")
    parser.add_argument("--show", action="store_true", help="print the Grasshopper record and exit")
    parser.add_argument("--check-names", action="store_true", help="verify existing class names against naming.py")
    args = parser.parse_args(argv)

    if args.check_names:
        return 1 if check_names(args.out) else 0
    if not args.name:
        parser.error("a Grasshopper component name is required (or --check-names)")

    record = find_record(load_records(args.dump), args.name, args.tab, args.sub, args.guid)
    if args.show:
        print(json.dumps(record, indent=1, ensure_ascii=False))
        return 0

    class_name = class_name_for(record["name"], record["category"], record["subcategory"], record["guid"])
    folder = SUBCATEGORY_FOLDERS.get(record["subcategory"], record["subcategory"])
    module_dir = args.out / record["category"] / folder
    module_path = module_dir / f"{class_name}.py"
    class_key = f"pyhopper.Components.{record['category']}.{folder}.{class_name}.{class_name}"
    inputs, variadic = build_inputs(record)
    outputs = build_outputs(record)

    print(f"{record['name']} ({record['nickname']}) -> {class_key}")
    for parent in (module_dir.parent, module_dir):
        init = parent / "__init__.py"
        if not init.exists():
            write(init, f'"""{parent.name} components."""\n', args.force, args.dry_run)
    write(module_path, render_module(record, class_name, inputs, outputs, variadic), args.force, args.dry_run)
    golden_path = args.golden / record["category"] / f"{class_name}.json"
    write(golden_path, render_golden(record, class_key, outputs), args.force, args.dry_run)
    oracle_path = args.oracle / record["category"] / f"{class_name}.json"
    write(oracle_path, render_oracle(record, class_key), args.force, args.dry_run)
    print(CHECKLIST.format(golden=_display(golden_path), oracle=_display(oracle_path), cls=class_name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
