"""Ad-hoc Grasshopper probes through the headless runner.

Edit PROBES, then run:  rhino-test\\.venv\\Scripts\\python rhino-test\\gh_probe.py
Each probe is (label, gh_guid, {input index: DataTree}); outputs are printed
with Grasshopper nulls kept so path/null behaviour is visible.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from oracle.gh_headless import solve_component  # noqa: E402

from pyhopper.Core.Atoms import AtomicInterval, AtomicLine, AtomicPoint  # noqa: E402
from tests.support.trees import tree  # noqa: E402

T = tree
SERIES = "e64c5fb1-845c-4ab1-8911-5f338516ba67"
PARTITION = "5a93246d-2595-4c28-bc2d-90657634f92a"
SPLIT = "9ab93e1a-ebdf-4090-9296-b000cff7b202"
CULL_INDEX = "501aecbb-c191-4d13-83d6-7ee32445ac50"
SUB_LIST = "b333ff42-93bd-406b-8e17-15780719b6ec"
LIST_ITEM = "59daf374-bc21-4a5e-8282-5504fb7ae9ae"
DIVIDE_CURVE = "2162e72e-72fc-4bf8-9459-d4d82fa8aa14"
RANGE = "9445ca40-cc73-4861-a455-146308676855"

PROBES = [
    ("List Item empty branch", LIST_ITEM, {0: T({"0": [], "1": ["a"]}), 1: T([0]), 2: T([False])}),
    ("Member Index empty branch", "3ff27857-b988-417a-b495-b24c733dbd00", {0: T({"0": [], "1": ["a", "b"]}), 1: T(["b"])}),
    ("Member Index two members", "3ff27857-b988-417a-b495-b24c733dbd00", {0: T(["a", "b", "a"]), 1: T(["a", "b"])}),
    ("Series empty count list", SERIES, {0: T([0.0]), 1: T([1.0]), 2: T({"0": []})}),
    ("Create Set", "98c3c63a-e78a-43ea-a111-514fcf312c95", {0: T([1, 2, 1, 3])}),
    ("Dispatch empty branch", "d8332545-21b2-4716-96e3-8559a9876e17", {0: T({"0": [], "1": [1, 2, 3]}), 1: T([True, False])}),
]

for label, guid, inputs in PROBES:
    try:
        outputs, messages = solve_component(guid, inputs, drop_nulls=False)
    except Exception as exc:  # keep probing
        print(f"## {label}\n  ERROR {exc!r}")
        continue
    print(f"## {label}")
    for name, out_tree in outputs.items():
        body = "; ".join(f"{path}: {list(branch)!r}" for path, branch in out_tree.branches()) or "<empty>"
        print(f"  {name}: {body}")
    if messages:
        print(f"  messages: {messages}")
