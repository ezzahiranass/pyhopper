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

from pyhopper.Core.Atoms import AtomicCircle, AtomicArc, AtomicPolyline, AtomicInterval as I, AtomicLine as L, AtomicVector as V, AtomicPlane
import math
EVAL = "fc6979e4-7e91-4508-8e05-37c680779751"
CRV_DOM = "ccfd6ba8-ecb1-44df-a47e-08126a653c51"
LEN_PARAM = "a1c16251-74f0-400f-9e7c-5e379d739963"
CLOSED = "323f3245-af49-4489-8677-7a2c73664077"
CTRL = "424eb433-2b3a-4859-beaf-804d8af0afd7"
PCEN = "59e94548-cefd-4774-b3de-48142fc783fb"
DIV_LEN = "fdc466a9-d3b8-4056-852a-09dba0f74aca"
PFRAMES = "983c7600-980c-44da-bc53-c804067f667f"
ARC = "bb59bffc-f54c-4682-9778-f6c3fe74fce3"
ARC3 = "9fa1b081-b1c7-4a12-a163-0aa8da9ff6c4"
ARCSED = "9d2583dd-6cf5-497c-8c40-c9a290598396"
REC2 = "575660b1-8c79-4b8d-9222-7ab4a6ddb359"
ENDS = "11bbd48b-bb0a-4f1b-8167-fa297590390d"
circle = AtomicCircle(AtomicPlane.world_xy(), 2.0)
line = L(P(0, 0, 0), P(4, 0, 0))
poly = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0)))
closed_poly = AtomicPolyline((P(0, 0, 0), P(2, 0, 0), P(2, 2, 0), P(0, 2, 0), P(0, 0, 0)))

from pyhopper.Core.Atoms import AtomicNurbsCurve
vertical = L(P(0, 0, 0), P(0, 0, 3))
helix = AtomicNurbsCurve((P(0, 0, 0), P(2, 0, 1), P(2, 2, 2), P(0, 2, 3), P(0, 0, 4), P(2, 0, 5)), (1.0,) * 6, (0, 0, 0, 0, 1, 2, 3, 3, 3, 3), 3)

diag = L(P(0, 0, 0), P(3, 3, 0))
yline = L(P(0, 0, 0), P(0, 3, 0))
uneven = AtomicPolyline((P(0, 0, 0), P(1, 0, 0), P(4, 0, 0)))
kinked = AtomicPolyline((P(0, 0, 0), P(4, 0, 0), P(4, 3, 0)))
from pyhopper.Core.Atoms import AtomicBox, AtomicSurface, AtomicTransform
BOX2 = "2a43ef96-8f87-4892-8b94-237a47e8d3cf"
BBOX = "0bb3d234-9097-45db-9998-621639c87d3b"
PLSRF = "439a55a5-2f9e-4f66-9de2-32f24fec2ef5"
DEBOX = "db7d83b1-2898-4ef9-9be5-4e94b4e2048d"
DIM = "f241e42e-8983-4ed3-b869-621c07630b00"
SRFPT = "15128198-399d-4d6c-9586-1f65db3ce7bf"
EXTRPT = "be6636b2-2f1a-4d42-897b-fdef429b6f17"
SUMSRF = "5e33c760-adcd-4235-b1dd-05cf72eb7a38"
LLX = "6d4b82a7-8c1d-4bec-af7b-ca321ba4beb1"
PLX = "75d0442c-1aa3-47cf-bd94-457b42c16e9f"
PPX = "290cf9c4-0711-4704-851e-4c99e3343ac5"
MTP = "4fe87ef8-49e4-4605-9859-87940d62e1de"
ROT3D = "3dfb9a77-6e05-4016-9f20-94f78607d672"
SHEAR = "5a27203a-e05f-4eea-b80f-a5f29a00fdf2"
PROJECT = "23285717-156c-468f-a691-b242488c06a6"
XFORM = "610e689b-5adc-47b3-af8f-e3a32b7ea341"
COMPOUND = "ca80054a-cde0-4f69-a132-10502b24866d"
INVERSE = "51f61166-7202-45aa-9126-3d83055b269e"
tilted = AtomicPlane(P(0, 0, 0), V(0, 1, 0), V(1, 0, 0))
plane_srf = AtomicSurface(poles=((P(0, 0, 0), P(4, 0, 0)), (P(0, 2, 0), P(4, 2, 0))), u_degree=1, v_degree=1)
curved = AtomicSurface(poles=((P(0, 0, 0), P(2, 0, 1), P(4, 0, 0)), (P(0, 2, 0), P(2, 2, 2), P(4, 2, 0))), u_degree=2, v_degree=1)
box = AtomicBox(AtomicPlane.world_xy(P(1, 1.5, 2)), 2.0, 3.0, 4.0)

curved2 = AtomicSurface(poles=((P(0, 0, 0), P(3, 0, 0), P(6, 0, 0)), (P(0, 1, 0), P(3, 1, 4), P(6, 1, 0))), u_degree=2, v_degree=1)
PROBES = [
    ("Dimensions curved2", DIM, {0: T([curved2])}),
    ("Dimensions plane rotated", DIM, {0: T([AtomicSurface(poles=((P(0, 0, 0), P(3, 4, 0)), (P(-4, 3, 0), P(-1, 7, 0))), u_degree=1, v_degree=1)])}),
    ("PPX other pair", PPX, {0: T([AtomicPlane(P(0, 0, 0), V(0, 0, 1), V(1, 0, 0))]), 1: T([AtomicPlane(P(3, 1, 2), V(0, 1, 0), V(1, 0, 0))])}),
    ("PPX tilted", PPX, {0: T([AtomicPlane(P(1, 1, 1), V(1, 1, 0), V(0, 0, 1))]), 1: T([AtomicPlane(P(-2, 0, 3), V(0, 0, 1), V(1, 0, 0))])}),
    ("MoveToPlane straddling below off", MTP, {0: T([L(P(0, 0, -1), P(0, 0, 3))]), 1: T([AtomicPlane.world_xy()]), 3: T([False])}),
    ("MoveToPlane straddling above off", MTP, {0: T([L(P(0, 0, -1), P(0, 0, 3))]), 1: T([AtomicPlane.world_xy()]), 2: T([False])}),
    ("MoveToPlane tilted plane point", MTP, {0: T([P(0, 5, 0)]), 1: T([AtomicPlane(P(0, 0, 0), V(0, 1, 0), V(1, 0, 0))])}),
    ("BBox nurbs", BBOX, {0: T([helix])}),
    ("BBox arc", BBOX, {0: T([AtomicArc(AtomicPlane.world_xy(), 2.0, I(0, math.pi / 2))])}),
    ("BBox box", BBOX, {0: T([box])}),
    ("BBox empty", BBOX, {0: T([])}),
    ("LLX param beyond both", LLX, {0: T([L(P(0, 0, 0), P(1, 0, 0))]), 1: T([L(P(3, 5, 0), P(3, 6, 0))])}),
    ("PLX line param beyond", PLX, {0: T([L(P(0, 0, 1), P(0, 0, 2))]), 1: T([AtomicPlane.world_xy()])}),
    ("Extrude point polyline", EXTRPT, {0: T([poly]), 1: T([P(1, 1, 5)])}),
    ("Extrude point surface", EXTRPT, {0: T([plane_srf]), 1: T([P(2, 1, 5)])}),
    ("Sum surface polyline line", SUMSRF, {0: T([poly]), 1: T([L(P(0, 0, 0), P(0, 0, 2))])}),
    ("Sum surface two arcs", SUMSRF, {0: T([AtomicArc(AtomicPlane.world_xy(), 1.0, I(0, math.pi / 2))]), 1: T([AtomicArc(AtomicPlane(P(0, 0, 0), V(0, 1, 0), V(1, 0, 0)), 1.0, I(0, math.pi / 2))])}),
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
