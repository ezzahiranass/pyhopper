"""Print Grasshopper's persistent input defaults for a list of components (headless).

Run:  rhino-test\\.venv\\Scripts\\python rhino-test\\gh_defaults.py "Dispatch" "Weave" ...
Without arguments it prints the Wave A2 Sets components.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from oracle.gh_headless import _params, load_grasshopper, to_python  # noqa: E402

DUMP = Path(__file__).resolve().parent / "gh_core_components_r8.json"
DEFAULT_NAMES = [
    "Dispatch", "Weave", "Sift Pattern", "Insert Items", "Replace Items", "Item Index", "Sort List",
    "Cull Pattern", "Cull Nth", "Repeat Data", "Duplicate Data", "Jitter", "Create Set", "Member Index",
    "Text Join", "Text Trim",
]


def persistent_defaults(guid: str) -> list[tuple[str, list]]:
    Grasshopper = load_grasshopper()
    import System  # type: ignore

    proxy = Grasshopper.Instances.ComponentServer.EmitObjectProxy(System.Guid(guid))
    component = proxy.CreateInstance()
    result = []
    for param in _params(component).Input:
        prop = param.GetType().GetProperty("PersistentData")
        values: list = []
        if prop is not None:
            data = prop.GetValue(param, None)
            if data is not None:
                for path in data.Paths:
                    for goo in data.get_Branch(path):
                        try:
                            values.append(to_python(goo))
                        except TypeError:
                            values.append(f"<{goo.GetType().Name}: {goo}>")  # e.g. culture info
        result.append((param.Name, values))
    return result


def main(names: list[str]) -> None:
    records = {(r["name"], r["category"]): r for r in json.loads(DUMP.read_text(encoding="utf-8"))}
    for name in names:
        matches = [r for (n, _), r in records.items() if n == name and r.get("inputs") is not None]
        for record in matches:
            print(f"## {record['category']} > {record['subcategory']} > {name}")
            for port, values in persistent_defaults(record["guid"]):
                print(f"  {port}: {values!r}")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT_NAMES)
