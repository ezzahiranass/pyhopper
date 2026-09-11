# Parametric Tower

A twisting tower with a columnar perimeter, a solid core, and a GLB export.
This is the canonical pyhopper example — every concept from the framework appears here.

```python title="Examples/first_test.py"
import math
from pyhopper import (
    CircleCmp, DivideCurve, Series, UnitZ, XYPlane,
    Move, Rotate, Polyline, CylinderCmp, LineCmp,
    Merge,
)
from pyhopper.Utils.Exporters import export_glb

NUM_FLOORS   = 20
NUM_COLUMNS  = 12
FLOOR_HEIGHT = 3.5   # m
BASE_RADIUS  = 20.0  # m
TWIST_DEG    = 3.0   # degrees per floor
CORE_RADIUS  = 6.0   # m

# ── 1. Base geometry ──────────────────────────────────────────────
base_circle  = CircleCmp(radius=BASE_RADIUS)
grid_points  = DivideCurve(base_circle, count=NUM_COLUMNS)
# grid_points: {0} → [P0 … P11]  (12 points on a circle of r=20; closed curves
# yield exactly `count` points, so the seam is not repeated)

# ── 2. Lift points to each floor level ───────────────────────────
levels       = Series(start=0, step=FLOOR_HEIGHT, count=NUM_FLOORS)
lift_vectors = UnitZ(levels.graft())
floor_points = Move(grid_points, lift_vectors)
# levels.graft():  {0;0}→[0]  {0;1}→[3.5]  …  {0;19}→[66.5]
# lift_vectors:    {0;0}→[(0,0,0)]  …  {0;19}→[(0,0,66.5)]
# floor_points:    20 branches × 12 pts = 240 Point3d

# ── 3. Rotate each floor ──────────────────────────────────────────
angles         = Series(start=0, step=math.radians(TWIST_DEG), count=NUM_FLOORS)
rotated_floors = Rotate(floor_points, angles.graft(), XYPlane())
# rotated_floors: same tree shape, each floor turned about world Z (angles in radians)

# ── 4. Close each floor into an outline ──────────────────────────
floor_polygons = Polyline(rotated_floors, closed=True)
# floor_polygons: 20 branches, 1 closed Polyline each

# ── 5. Vertical columns ───────────────────────────────────────────
top_points = Move(grid_points, UnitZ(FLOOR_HEIGHT * NUM_FLOORS))
columns    = LineCmp(grid_points, top_points)
# columns: {0} → 12 Line atoms

# ── 6. Central core ───────────────────────────────────────────────
core = CylinderCmp(radius=CORE_RADIUS, length=FLOOR_HEIGHT * NUM_FLOORS)

# ── 7. Merge and export ───────────────────────────────────────────
tower = Merge(floor_polygons, columns, core)
export_glb(tower, "tower.glb")
```

---

## Data flow diagram

```
CircleCmp(r=20)                    → {0}: [Circle]
    │
    └─ DivideCurve(n=12)           → {0}: [P0…P11]  12 pts
           │
           ├─ Move(UnitZ(levels↑)) ← levels = Series(0, 3.5, 20).graft()
           │                       → {0;0}…{0;19}: [P0…P11] each  (240 pts)
           │       │
           │       └─ Rotate(angles↑, XYPlane)  ← angles = Series(0, 3°, 20).graft()
           │                                    → 240 rotated pts, same structure
           │               │
           │               └─ Polyline(closed)  → {0;0}…{0;19}: [Polyline]  (20 floors)
           │
           └─ Move(UnitZ(70))      → {0}: [P0'…P11']  top pts
                   │
                   └─ LineCmp      → {0}: [L0…L11]  12 columns

CylinderCmp(r=6, length=70)        → {0}: [Surface]

Merge(floors, columns, core)       → {0;0}…{0;19}: [Polyline]
                                      {0}: [L0…L11, Surface]
    │
    └─ export_glb → tower.glb
```

---

## What to try next

- Change `TWIST_DEG` to `0` — all floors align, no twist
- Change `NUM_COLUMNS` to `6` — hexagonal floor plate
- Add a `Loft` component between floors to create a surface skin
- Increase `NUM_FLOORS` and `BASE_RADIUS` — everything scales automatically
