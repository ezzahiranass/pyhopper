# Getting Started

## Installation

```bash
pip install pyhopper
```

pyhopper has no mandatory dependencies beyond the standard library.
Optional geometry backends (`shapely`, `build123d`) unlock more components.

---

## Your first model

We'll build a minimal twisted column grid — the same idea as the bundled tower example, reduced to its essence.

### 1. Create a base circle and divide it

```python
from pyhopper import CircleCmp, DivideCurve

circle = CircleCmp(radius=10)
points = DivideCurve(circle, count=8)
# points is a DataTree: 1 branch {0}, 8 Point3d items
```

`CircleCmp` produces a `Circle` atom.
`DivideCurve` samples it at `count` evenly-spaced parameter values and returns `Point3d` atoms.

### 2. Stack points vertically

```python
from pyhopper import Series, UnitZ, Move

z      = UnitZ()                               # DataTree: 1 Vector3d (0,0,1)
levels = Series(start=0, step=3.0, count=10)  # DataTree: 10 floats
floors = Move(points, z, levels.graft())
# floors: 10 branches {0;0}…{0;9}, 8 Point3d each = 80 points
```

`levels.graft()` turns the flat list of 10 heights into 10 **branches of 1 item each**.
When `Move` sees 10 branches on one input and 1 branch on the other, it repeats the
single branch for every step — producing one translated copy of the 8 base points
for each floor level.

### 3. Close each floor into a polygon

```python
from pyhopper import Polygon

polys = Polygon(floors)
# polys: 10 branches, 1 Polyline each
```

`Polygon` uses `LIST` access — it receives the full list of points per branch and
returns one closed `Polyline` per floor.

### 4. Export to GLB

```python
from pyhopper.Utils.Exporters import export_glb

export_glb(polys, "column_grid.glb")
```

Open the file in any glTF viewer (Babylon.js sandbox, Blender, three.js editor).

---

## Understanding the flow

```
CircleCmp(r=10)           → DataTree {0}: [Circle]
    ↓ DivideCurve(n=8)
                           → DataTree {0}: [P0, P1, … P7]  (8 pts)
    ↓ Move(z, levels.graft())
    levels = [0,3,6,…27]  → DataTree {0;0}…{0;9}: [P0…P7] per floor
    ↓ Polygon
                           → DataTree {0;0}…{0;9}: [Polyline] per floor
```

The tree structure is the memory of *where* data came from. When you graft, each
item splits into its own branch so the next component can address them individually.

---

## Next steps

- Read [Concepts → Data Tree](concepts/data-tree.md) to understand branching deeply
- See the full [Parametric Tower example](examples/tower.md) with rotation and export
- Browse the [Reference](reference/) for every component's inputs and outputs
