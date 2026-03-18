# pyhopper

**Declarative parametric 3D modeling in Python.**

pyhopper brings the node-graph paradigm of [Grasshopper3D](https://www.rhino3d.com/6/new/grasshopper/) into pure Python. You define a model by composing *components* — each one a small, testable function that reads from and writes to **DataTrees** — just like wiring nodes on a Grasshopper canvas.

```python
from pyhopper import (
    CircleCmp, DivideCurve, Series, UnitZ,
    Move, Rotate, Polygon, Merge,
)

base   = CircleCmp(radius=20)
pts    = DivideCurve(base, count=12)
z      = UnitZ()
levels = Series(start=0, step=3.5, count=20)
angles = Series(start=0, step=3,   count=20)

floors  = Move(pts, z, levels.graft())
twisted = Rotate(floors, axis=z, angle=angles.graft())
polys   = Polygon(twisted)
tower   = Merge(polys)
```

---

## Key ideas

| Concept | Description |
|---------|-------------|
| **Atom** | Immutable geometric primitive (`Point3d`, `Line`, `Circle`, `Polyline`, …) |
| **DataTree** | Hierarchical container of Atoms — the unit of exchange between components |
| **Branch / Path** | A branch is a list of items at an address `{0;2;1}` inside a DataTree |
| **Component** | A processing node — takes DataTrees in, returns a DataTree out |
| **Graft / Flatten** | Tree operations that reshape data before it flows into the next component |

---

## Install

```bash
pip install pyhopper
```

Or from source:

```bash
git clone https://github.com/your-org/pyhopper
pip install -e .
```

---

## Quick links

- [Getting Started](getting-started.md) — your first model in 10 minutes
- [Concepts](concepts/index.md) — understand DataTrees and how components work
- [Reference](reference/) — full auto-generated API docs
- [Examples](examples/tower.md) — annotated real-world models
