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

CP = "571ca323-6e55-425a-bf9e-ee103c7ba4b9"
CPS = "446014c4-c11c-45a7-8839-c45dc60950d6"
CULL_DUP = "6eaffbb2-3392-441a-8556-2dc126aa8910"
POLAR = "a435f5c8-28a2-43e8-a52a-0b6e73c2e300"
SORT_PTS = "4e86ba36-05e2-4cc0-a0f5-3ad57c91f04e"
PL_NORMAL = "cfb6b17f-ca82-4f5d-b604-d4f69f569de3"
PL_3PT = "c98a6015-7a2f-423c-bc66-bdc505249b45"
ALIGN = "e76040ec-3b91-41e1-8e00-c74c23b89391"
REC_GRID = "1a25aae0-0b56-497a-85b2-cc5bf7e4b96b"
SQ_GRID = "717a1e25-a075-4530-bc80-d43ecc2500d9"
POP2D = "e2d958e8-9f08-44f7-bf47-a684882d0b2a"
from pyhopper.Core.Atoms import AtomicVector as V, AtomicPlane, AtomicRectangle
import math

PROBES = [
    ("CP tie", CP, {0: T([P(0, 0, 0)]), 1: T([P(1, 0, 0), P(0, 2, 0), P(-1, 0, 0)])}),
    ("CP empty cloud", CP, {0: T([P(0, 0, 0)]), 1: T([])}),
    ("CPs count 2", CPS, {0: T([P(0, 0, 0)]), 1: T([P(3, 0, 0), P(1, 0, 0), P(0, 2, 0)]), 2: T([2])}),
    ("CPs count exceeds cloud", CPS, {0: T([P(0, 0, 0)]), 1: T([P(3, 0, 0), P(1, 0, 0)]), 2: T([5])}),
    ("CPs two points", CPS, {0: T([P(0, 0, 0), P(10, 0, 0)]), 1: T([P(3, 0, 0), P(1, 0, 0), P(9, 0, 0)]), 2: T([2])}),
    ("Cull dup", CULL_DUP, {0: T([P(0, 0, 0), P(0, 0, 0.0005), P(1, 0, 0), P(0, 0, 0), P(1, 0.0004, 0)]), 1: T([0.001])}),
    ("Cull dup chain", CULL_DUP, {0: T([P(0, 0, 0), P(0.0008, 0, 0), P(0.0016, 0, 0)]), 1: T([0.001])}),
    ("Cull dup none", CULL_DUP, {0: T([P(0, 0, 0), P(5, 0, 0)]), 1: T([0.001])}),
    ("Polar", POLAR, {1: T([math.pi / 2]), 2: T([0.0]), 3: T([2.0])}),
    ("Polar z angle", POLAR, {1: T([0.0]), 2: T([math.pi / 4]), 3: T([2.0])}),
    ("Sort points", SORT_PTS, {0: T([P(1, 0, 0), P(0, 5, 0), P(0, 0, 3), P(0, 0, 1), P(0, 0, 1)])}),
    ("Plane normal z", PL_NORMAL, {0: T([P(1, 2, 3)]), 1: T([V(0, 0, 1)])}),
    ("Plane normal tilted", PL_NORMAL, {0: T([P(0, 0, 0)]), 1: T([V(1, 1, 0)])}),
    ("Plane normal x", PL_NORMAL, {0: T([P(0, 0, 0)]), 1: T([V(1, 0, 0)])}),
    ("Plane normal generic", PL_NORMAL, {0: T([P(0, 0, 0)]), 1: T([V(0.3, -0.5, 0.8)])}),
    ("Plane normal zero", PL_NORMAL, {0: T([P(0, 0, 0)]), 1: T([V(0, 0, 0)])}),
    ("Plane 3pt", PL_3PT, {0: T([P(0, 0, 0)]), 1: T([P(2, 0, 0)]), 2: T([P(0, 3, 0)])}),
    ("Plane 3pt other side", PL_3PT, {0: T([P(0, 0, 0)]), 1: T([P(2, 0, 0)]), 2: T([P(1, -3, 0)])}),
    ("Plane 3pt collinear", PL_3PT, {0: T([P(0, 0, 0)]), 1: T([P(1, 0, 0)]), 2: T([P(2, 0, 0)])}),
    ("Align xy to y", ALIGN, {0: T([AtomicPlane.world_xy()]), 1: T([V(0, 1, 0)])}),
    ("Align xy to diag", ALIGN, {0: T([AtomicPlane.world_xy()]), 1: T([V(1, 1, 0)])}),
    ("Align xy to tilted", ALIGN, {0: T([AtomicPlane.world_xy()]), 1: T([V(0, 1, 1)])}),
    ("Align xy to -x", ALIGN, {0: T([AtomicPlane.world_xy()]), 1: T([V(-1, 0, 0)])}),
    ("Align xy to normal", ALIGN, {0: T([AtomicPlane.world_xy()]), 1: T([V(0, 0, 1)])}),
    ("Align xy to -y", ALIGN, {0: T([AtomicPlane.world_xy()]), 1: T([V(0, -1, 0)])}),
    ("Rec grid 2x3 sizes 2,1", REC_GRID, {1: T([2.0]), 2: T([1.0]), 3: T([2]), 4: T([3])}),
    ("Rec grid 1x1", REC_GRID, {1: T([2.0]), 2: T([1.0]), 3: T([1]), 4: T([1])}),
    ("Rec grid 0 extent", REC_GRID, {1: T([2.0]), 2: T([1.0]), 3: T([0]), 4: T([2])}),
    ("Rec grid two sizes", REC_GRID, {1: T([1.0, 2.0]), 2: T([1.0]), 3: T([1]), 4: T([1])}),
    ("Sq grid 2x1", SQ_GRID, {1: T([3.0]), 2: T([2]), 3: T([1])}),
    ("Pop2D 5", POP2D, {0: T([AtomicRectangle(AtomicPlane.world_xy(P(5, 5, 0)), 10.0, 10.0)]), 1: T([5]), 2: T([1])}),
    ("Pop2D seed points", POP2D, {0: T([AtomicRectangle(AtomicPlane.world_xy(P(5, 5, 0)), 10.0, 10.0)]), 1: T([4]), 2: T([1]), 3: T([P(5, 5, 0)])}),
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
