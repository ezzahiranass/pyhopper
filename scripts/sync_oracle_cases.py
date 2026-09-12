"""Mirror golden fixture inputs into the Rhino/Grasshopper oracle case files.

Golden fixtures (``tests/golden/components/<Tab>/<Class>.json``) are the
hand-authored source of inputs; the oracle case files
(``rhino-test/oracle/cases/<Tab>/<Class>.json``) feed the same inputs to
Grasshopper. This script copies every non-raising golden case into the oracle
file, keeping the oracle-only knobs already there: fixture-level ``mode``,
``tolerance``, ``paths``, ``notes`` and per-case ``gh`` options (``{"skip":
"reason"}`` for documented deviations).

Usage:
    .venv\\Scripts\\python scripts/sync_oracle_cases.py [Tab/Class ...]

Without arguments every oracle file that has a golden twin is synchronised.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = REPO_ROOT / "tests" / "golden" / "components"
ORACLE_ROOT = REPO_ROOT / "rhino-test" / "oracle" / "cases"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def sync(relative: str) -> int:
    """Return the number of cases written for ``Tab/Class``."""
    golden = _load(GOLDEN_ROOT / f"{relative}.json")
    oracle_path = ORACLE_ROOT / f"{relative}.json"
    oracle = _load(oracle_path)
    previous = {case["name"]: case for case in oracle.get("cases", [])}
    compare = next((case["compare"] for case in oracle.get("cases", []) if case.get("compare")), None)

    cases = []
    for case in golden["cases"]:
        if case.get("raises"):
            continue  # exceptions have no Grasshopper counterpart
        entry = {"name": case["name"], "inputs": case.get("inputs", {})}
        if case.get("settings"):
            entry["settings"] = case["settings"]
        if compare:
            entry["compare"] = compare
        if "gh" in previous.get(case["name"], {}):
            entry["gh"] = previous[case["name"]]["gh"]
        cases.append(entry)
    oracle["cases"] = cases
    _save(oracle_path, oracle)
    return len(cases)


def main(argv: list[str]) -> int:
    if argv:
        targets = argv
    else:
        targets = sorted(
            path.relative_to(ORACLE_ROOT).with_suffix("").as_posix()
            for path in ORACLE_ROOT.rglob("*.json")
            if (GOLDEN_ROOT / path.relative_to(ORACLE_ROOT)).exists()
        )
    total = 0
    for relative in targets:
        count = sync(relative)
        total += count
        print(f"{relative}: {count} cases")
    print(f"synchronised {len(targets)} oracle files, {total} cases")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
