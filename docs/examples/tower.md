# Parametric Tower

A twisting tower with a columnar perimeter, a solid core, and a GLB export.
This is the canonical pyhopper example — every concept from the framework appears here.

```python title="Examples/first_test.py"
from pyhopper import (
    CircleCmp, DivideCurve, Series, UnitZ,
    Move, Rotate, Polygon, CylinderCmp, LineCmp,
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
# grid_points: {0} → [P0 … P11]  (12 points on a circle of r=20)

# ── 2. Unit vectors ───────────────────────────────────────────────
z_vec = UnitZ()
# z_vec: {0} → [Vector3d(0,0,1)]  — reused as a DataTree throughout

# ── 3. Lift points to each floor level ───────────────────────────
levels       = Series(start=0, step=FLOOR_HEIGHT, count=NUM_FLOORS)
floor_points = Move(grid_points, z_vec, levels.graft())
# levels.graft(): {0;0}→[0]  {0;1}→[3.5]  …  {0;19}→[66.5]
# floor_points:   20 branches × 12 pts = 240 Point3d

# ── 4. Rotate each floor ──────────────────────────────────────────
angles         = Series(start=0, step=TWIST_DEG, count=NUM_FLOORS)
rotated_floors = Rotate(floor_points, axis=z_vec, angle=angles.graft())
# rotated_floors: same tree shape, points rotated per branch

# ── 5. Close each floor into a polygon ───────────────────────────
floor_polygons = Polygon(rotated_floors)
# floor_polygons: 20 branches, 1 Polyline each

# ── 6. Vertical columns ───────────────────────────────────────────
top_points = Move(grid_points, z_vec, FLOOR_HEIGHT * NUM_FLOORS)
columns    = LineCmp(grid_points, top_points)
# columns: {0} → 12 Line atoms

# ── 7. Central core ───────────────────────────────────────────────
core = CylinderCmp(radius=CORE_RADIUS, height=FLOOR_HEIGHT * NUM_FLOORS)

# ── 8. Merge and export ───────────────────────────────────────────
tower = Merge(floor_polygons, columns, core)
export_glb(tower, "tower.glb")
```

---

## Data flow diagram

```
CircleCmp(r=20)                 → {0}: [Circle]
    │
    └─ DivideCurve(n=12)        → {0}: [P0…P11]  12 pts
           │
           ├─ Move(z, levels↑)  ← levels = Series(0, 3.5, 20).graft()
           │                    → {0;0}…{0;19}: [P0…P11] each  (240 pts)
           │       │
           │       └─ Rotate(z, angles↑)  ← angles = Series(0, 3°, 20).graft()
           │                              → 240 rotated pts, same structure
           │               │
           │               └─ Polygon     → {0;0}…{0;19}: [Polyline]  (20 floors)
           │
           └─ Move(z, 70)       → {0}: [P0'…P11']  top pts
                   │
                   └─ LineCmp   → {0}: [L0…L11]  12 columns

CylinderCmp(r=6, h=70)          → {0}: [Cylinder]

Merge(floors, columns, core)    → {0;0}…{0;19}: [Polyline]
                                   {0}: [L0…L11, Cylinder]
    │
    └─ export_glb → tower.glb
```

---

## What to try next

- Change `TWIST_DEG` to `0` — all floors align, no twist
- Change `NUM_COLUMNS` to `6` — hexagonal floor plate
- Add a `Loft` component between floors to create a surface skin
- Increase `NUM_FLOORS` and `BASE_RADIUS` — everything scales automatically
