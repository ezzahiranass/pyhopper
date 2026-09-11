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

FLATTEN = "f80cfe18-9510-4b89-8301-8e58faf423bb"
GRAFT = "87e1d9ef-088b-4d30-9dda-8a7448a17329"
SIMPLIFY = "1303da7b-e339-4e65-a051-82c4dce8224d"
TRIM = "1177d6ee-3993-4226-9558-52b7fd63e1e3"
FLIP = "41aa4112-9c9b-42f4-847e-503b9d90e4c7"
ENTWINE = "c9785b8e-2f30-4f90-8ee3-cca710f82402"
PRUNE = "fe769f85-8900-45dd-ba11-ec9cd6c778c6"
CLEAN = "071c3940-a12d-4b77-bb23-42b5d3314a0d"
from pyhopper.Core.Path import Path as TP

PROBES = [
    ("Simplify single {0;0}", SIMPLIFY, {0: T({"0;0": ["a", "b"]})}),
    ("Simplify single {0;0} front", SIMPLIFY, {0: T({"0;0": ["a", "b"]}), 1: T([True])}),
    ("Simplify single {0}", SIMPLIFY, {0: T({"0": ["a", "b"]})}),
    ("Simplify single {0;0;0}", SIMPLIFY, {0: T({"0;0;0": ["a"]})}),
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
