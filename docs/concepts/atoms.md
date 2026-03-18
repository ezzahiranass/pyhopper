# Atoms

Atoms are the **indivisible data units** that flow through DataTrees. They are frozen
dataclasses — immutable, hashable, and directly serializable to JSON.

No geometry operations live on Atoms. All transformations belong in Components.

---

## Built-in atoms

| Atom | Description |
|------|-------------|
| `Point3d` | A point in 3D space `(x, y, z)` |
| `Vector3d` | A direction vector `(x, y, z)` |
| `Interval` | A numeric domain `[start, end]` |
| `Plane` | An oriented coordinate frame (origin + normal + x-axis) |
| `Line` | A line segment between two `Point3d` values |
| `Circle` | A circle defined by a `Plane` and a radius |
| `Arc` | A circular arc defined by a `Plane`, radius, and angle interval |
| `Polyline` | An ordered sequence of `Point3d` values (optionally closed) |
| `NurbsCurve` | A NURBS curve (control points, weights, knots, degree) |
| `Mesh` | A polygonal mesh (vertices + face index lists) |
| `Surface` | A NURBS surface (control point grid, degree U/V) |
| `Cylinder` | A cylinder defined by a `Plane`, radius, and height |

---

## Using atoms directly

Atoms are plain Python objects:

```python
from pyhopper import Point3d, Vector3d, Plane

pt  = Point3d(1.0, 2.0, 3.0)
vec = Vector3d(0, 0, 1).unitize()
pln = Plane.world_xy()

pt.x          # 1.0
vec.length    # 1.0
pln.y_axis    # Vector3d(0, 1, 0)
```

---

## Serialization

Every Atom serializes to a plain dict with a `"type"` key:

```python
pt = Point3d(1, 2, 3)
pt.to_json()
# {"type": "Point3d", "x": 1.0, "y": 2.0, "z": 3.0}

Point3d.from_json({"type": "Point3d", "x": 1.0, "y": 2.0, "z": 3.0})
# Point3d(x=1.0, y=2.0, z=3.0)
```

The global `ATOM_REGISTRY` maps type strings to classes, so DataTree deserialization
dispatches automatically — you never need to specify the class manually.

---

## Defining a custom Atom

Subclass `Atom`, decorate with `@dataclass(frozen=True)`, set `atom_type`, and
implement `to_json` / `from_json`. It auto-registers.

```python
from dataclasses import dataclass
from typing import ClassVar
from pyhopper import Atom

@dataclass(frozen=True)
class ColoredPoint(Atom):
    atom_type: ClassVar[str] = "ColoredPoint"

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    r: int = 255
    g: int = 255
    b: int = 255

    def to_json(self) -> dict:
        return {"type": "ColoredPoint",
                "x": self.x, "y": self.y, "z": self.z,
                "r": self.r, "g": self.g, "b": self.b}

    @classmethod
    def from_json(cls, data: dict) -> "ColoredPoint":
        return cls(data["x"], data["y"], data["z"],
                   data["r"], data["g"], data["b"])
```

---

## API reference

See the full [Atoms reference](../reference/Core/Atoms.md).
