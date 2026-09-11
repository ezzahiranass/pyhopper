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

DISPATCH = "d8332545-21b2-4716-96e3-8559a9876e17"
WEAVE = "50faccbd-9c92-4175-a5fa-d65e36013db6"
SIFT = "3249222f-f536-467a-89f4-f0353fba455a"
INSERT = "e2039b07-d3f3-40f8-af88-d74fed238727"
REPLACE = "7a218bfb-b93d-4c1f-83d3-5a0b909dd60b"
ITEM_INDEX = "a759fd55-e6be-4673-8365-c28d5b52c6c0"
SORT = "6f93d366-919f-4dda-a35e-ba03dd62799b"
CULL_PATTERN = "008e9a6f-478a-4813-8c8a-546273bc3a6b"
CULL_NTH = "932b9817-fcc6-4ac3-b5fd-c0e8eeadc53f"
REPEAT = "c40dc145-9e36-4a69-ac1a-6d825c654993"
DUPLICATE = "dd8134c0-109b-4012-92be-51d843edfff7"
JITTER = "f02a20f6-bb49-4e3d-b155-8ed5d3c6b000"
CREATE_SET = "98c3c63a-e78a-43ea-a111-514fcf312c95"
MEMBER_INDEX = "3ff27857-b988-417a-b495-b24c733dbd00"
TEXT_JOIN = "1274d51a-81e6-4ccf-ad1f-0edf4c769cac"
TEXT_TRIM = "e4cb7168-5e32-4c54-b425-5a31c6fd685a"
P = AtomicPoint

PROBES = [
    ("Text Join floats", TEXT_JOIN, {0: T([1.0, 2.50, -0.5, 1e-7, 123456789.0, 0.1 + 0.2]), 1: T(["|"])}),
    ("Sort unique keys with values", SORT, {0: T([3.0, 1.0, 2.0]), 1: T(["c", "a", "b"])}),
    ("Sort dup keys with values", SORT, {0: T([2.0, 1.0, 2.0, 1.0]), 1: T(["w", "x", "y", "z"])}),
    ("Sort ints", SORT, {0: T([3, 1, 2])}),
    ("Sort negative and reversed", SORT, {0: T([0.5, -1.0, -1.0, 10.0])}),
    ("Sift pattern longer than list", SIFT, {0: T(["a", "b"]), 1: T([1, 1, 0, 0])}),
    ("Weave streams empty", WEAVE, {0: T([0, 1]), 1: T([]), 2: T(["x", "y"])}),
    ("Repeat empty list", REPEAT, {0: T([]), 1: T([3])}),
    ("Cull Pattern empty pattern", CULL_PATTERN, {0: T(["a", "b"]), 1: T([])}),
    ("Jitter half", JITTER, {0: T(["a", "b", "c", "d", "e", "f", "g", "h"]), 1: T([0.5]), 2: T([1])}),
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
