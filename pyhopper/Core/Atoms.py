"""
Atoms - Immutable geometric primitives for pyhopper.

Atoms are the indivisible data units that flow through DataTrees.
They are pure data containers with no behavior — all operations
live in Components and Adapters.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import ClassVar

# Global registry: atom_type string -> class
ATOM_REGISTRY: dict[str, type] = {}


class Atom:
    """Base class for all geometric primitives.

    Subclasses must be frozen dataclasses and define atom_type as a ClassVar.
    They auto-register into ATOM_REGISTRY via __init_subclass__.
    """

    atom_type: ClassVar[str] = "Atom"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "atom_type") and cls.atom_type != "Atom":
            ATOM_REGISTRY[cls.atom_type] = cls

    def to_json(self) -> dict:
        raise NotImplementedError

    @classmethod
    def from_json(cls, data: dict) -> Atom:
        raise NotImplementedError


# ── Concrete Atoms ──────────────────────────────────────────────────


@dataclass(frozen=True)
class AtomicPoint(Atom):
    atom_type: ClassVar[str] = "Point3d"

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_json(self) -> dict:
        return {"type": "Point3d", "x": self.x, "y": self.y, "z": self.z}

    @classmethod
    def from_json(cls, data: dict) -> AtomicPoint:
        return cls(x=data["x"], y=data["y"], z=data["z"])

    @classmethod
    def origin(cls) -> AtomicPoint:
        return cls(0.0, 0.0, 0.0)


@dataclass(frozen=True)
class AtomicVector(Atom):
    atom_type: ClassVar[str] = "Vector3d"

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_json(self) -> dict:
        return {"type": "Vector3d", "x": self.x, "y": self.y, "z": self.z}

    @classmethod
    def from_json(cls, data: dict) -> AtomicVector:
        return cls(x=data["x"], y=data["y"], z=data["z"])

    @property
    def length(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def unitize(self) -> AtomicVector:
        ln = self.length
        if ln == 0:
            return AtomicVector(0.0, 0.0, 0.0)
        return AtomicVector(self.x / ln, self.y / ln, self.z / ln)

    @classmethod
    def unit_x(cls) -> AtomicVector:
        return cls(1.0, 0.0, 0.0)

    @classmethod
    def unit_y(cls) -> AtomicVector:
        return cls(0.0, 1.0, 0.0)

    @classmethod
    def unit_z(cls) -> AtomicVector:
        return cls(0.0, 0.0, 1.0)


@dataclass(frozen=True)
class AtomicInterval(Atom):
    """A numeric domain / interval (Grasshopper's Domain)."""

    atom_type: ClassVar[str] = "Interval"

    start: float = 0.0
    end: float = 1.0

    def to_json(self) -> dict:
        return {"type": "Interval", "start": self.start, "end": self.end}

    @classmethod
    def from_json(cls, data: dict) -> AtomicInterval:
        return cls(start=data["start"], end=data["end"])

    @property
    def length(self) -> float:
        return self.end - self.start

    @property
    def mid(self) -> float:
        return (self.start + self.end) / 2.0

    def remap(self, t: float) -> float:
        """Map a value from [0, 1] into this interval."""
        return self.start + t * self.length


@dataclass(frozen=True)
class AtomicPlane(Atom):
    atom_type: ClassVar[str] = "Plane"

    origin: AtomicPoint = None  # type: ignore[assignment]
    normal: AtomicVector = None  # type: ignore[assignment]
    x_axis: AtomicVector = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.origin is None:
            object.__setattr__(self, "origin", AtomicPoint.origin())
        if self.normal is None:
            object.__setattr__(self, "normal", AtomicVector.unit_z())
        if self.x_axis is None:
            object.__setattr__(self, "x_axis", AtomicVector.unit_x())

    @property
    def y_axis(self) -> AtomicVector:
        # cross product of normal and x_axis
        n, x = self.normal, self.x_axis
        return AtomicVector(
            n.y * x.z - n.z * x.y,
            n.z * x.x - n.x * x.z,
            n.x * x.y - n.y * x.x,
        )

    def to_json(self) -> dict:
        return {
            "type": "Plane",
            "origin": self.origin.to_json(),
            "normal": self.normal.to_json(),
            "x_axis": self.x_axis.to_json(),
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicPlane:
        return cls(
            origin=AtomicPoint.from_json(data["origin"]),
            normal=AtomicVector.from_json(data["normal"]),
            x_axis=AtomicVector.from_json(data["x_axis"]),
        )

    @classmethod
    def world_xy(cls) -> AtomicPlane:
        return cls(AtomicPoint.origin(), AtomicVector.unit_z(), AtomicVector.unit_x())

    @classmethod
    def world_xz(cls) -> AtomicPlane:
        return cls(AtomicPoint.origin(), AtomicVector.unit_y(), AtomicVector.unit_x())

    @classmethod
    def world_yz(cls) -> AtomicPlane:
        return cls(AtomicPoint.origin(), AtomicVector.unit_x(), AtomicVector.unit_y())


@dataclass(frozen=True)
class AtomicLine(Atom):
    atom_type: ClassVar[str] = "Line"

    start: AtomicPoint = None  # type: ignore[assignment]
    end: AtomicPoint = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.start is None:
            object.__setattr__(self, "start", AtomicPoint.origin())
        if self.end is None:
            object.__setattr__(self, "end", AtomicPoint(1.0, 0.0, 0.0))

    @property
    def length(self) -> float:
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        dz = self.end.z - self.start.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    @property
    def direction(self) -> AtomicVector:
        return AtomicVector(
            self.end.x - self.start.x,
            self.end.y - self.start.y,
            self.end.z - self.start.z,
        )

    @property
    def midpoint(self) -> AtomicPoint:
        return AtomicPoint(
            (self.start.x + self.end.x) / 2,
            (self.start.y + self.end.y) / 2,
            (self.start.z + self.end.z) / 2,
        )

    def to_json(self) -> dict:
        return {
            "type": "Line",
            "start": self.start.to_json(),
            "end": self.end.to_json(),
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicLine:
        return cls(
            start=AtomicPoint.from_json(data["start"]),
            end=AtomicPoint.from_json(data["end"]),
        )


@dataclass(frozen=True)
class AtomicCircle(Atom):
    atom_type: ClassVar[str] = "Circle"

    plane: AtomicPlane = None  # type: ignore[assignment]
    radius: float = 1.0

    def __post_init__(self):
        if self.plane is None:
            object.__setattr__(self, "plane", AtomicPlane.world_xy())

    @property
    def center(self) -> AtomicPoint:
        return self.plane.origin

    @property
    def circumference(self) -> float:
        return 2.0 * math.pi * self.radius

    @property
    def area(self) -> float:
        return math.pi * self.radius ** 2

    def to_json(self) -> dict:
        return {
            "type": "Circle",
            "plane": self.plane.to_json(),
            "radius": self.radius,
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicCircle:
        return cls(
            plane=AtomicPlane.from_json(data["plane"]),
            radius=data["radius"],
        )


@dataclass(frozen=True)
class AtomicArc(Atom):
    atom_type: ClassVar[str] = "Arc"

    plane: AtomicPlane = None  # type: ignore[assignment]
    radius: float = 1.0
    angle: AtomicInterval = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.plane is None:
            object.__setattr__(self, "plane", AtomicPlane.world_xy())
        if self.angle is None:
            object.__setattr__(self, "angle", AtomicInterval(0.0, math.pi))

    def to_json(self) -> dict:
        return {
            "type": "Arc",
            "plane": self.plane.to_json(),
            "radius": self.radius,
            "angle": self.angle.to_json(),
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicArc:
        return cls(
            plane=AtomicPlane.from_json(data["plane"]),
            radius=data["radius"],
            angle=AtomicInterval.from_json(data["angle"]),
        )


@dataclass(frozen=True)
class AtomicPolyline(Atom):
    atom_type: ClassVar[str] = "Polyline"

    points: tuple[AtomicPoint, ...] = ()

    @property
    def count(self) -> int:
        return len(self.points)

    @property
    def is_closed(self) -> bool:
        if len(self.points) < 3:
            return False
        return self.points[0] == self.points[-1]

    def to_json(self) -> dict:
        return {
            "type": "Polyline",
            "points": [p.to_json() for p in self.points],
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicPolyline:
        pts = tuple(AtomicPoint.from_json(p) for p in data["points"])
        return cls(points=pts)


@dataclass(frozen=True)
class AtomicNurbsCurve(Atom):
    """General NURBS curve representation."""

    atom_type: ClassVar[str] = "NurbsCurve"

    control_points: tuple[AtomicPoint, ...] = ()
    weights: tuple[float, ...] = ()
    knots: tuple[float, ...] = ()
    degree: int = 3

    def to_json(self) -> dict:
        return {
            "type": "NurbsCurve",
            "control_points": [p.to_json() for p in self.control_points],
            "weights": list(self.weights),
            "knots": list(self.knots),
            "degree": self.degree,
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicNurbsCurve:
        return cls(
            control_points=tuple(
                AtomicPoint.from_json(p) for p in data["control_points"]
            ),
            weights=tuple(data["weights"]),
            knots=tuple(data["knots"]),
            degree=data["degree"],
        )


@dataclass(frozen=True)
class AtomicMesh(Atom):
    """Polygonal mesh."""

    atom_type: ClassVar[str] = "Mesh"

    vertices: tuple[AtomicPoint, ...] = ()
    faces: tuple[tuple[int, ...], ...] = ()

    def to_json(self) -> dict:
        return {
            "type": "Mesh",
            "vertices": [v.to_json() for v in self.vertices],
            "faces": [list(f) for f in self.faces],
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicMesh:
        return cls(
            vertices=tuple(AtomicPoint.from_json(v) for v in data["vertices"]),
            faces=tuple(tuple(f) for f in data["faces"]),
        )


@dataclass(frozen=True)
class AtomicSurface(Atom):
    """NURBS surface representation."""

    atom_type: ClassVar[str] = "Surface"

    control_points: tuple[tuple[AtomicPoint, ...], ...] = ()
    degree_u: int = 3
    degree_v: int = 3

    def to_json(self) -> dict:
        return {
            "type": "Surface",
            "control_points": [
                [p.to_json() for p in row] for row in self.control_points
            ],
            "degree_u": self.degree_u,
            "degree_v": self.degree_v,
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicSurface:
        return cls(
            control_points=tuple(
                tuple(AtomicPoint.from_json(p) for p in row)
                for row in data["control_points"]
            ),
            degree_u=data["degree_u"],
            degree_v=data["degree_v"],
        )


@dataclass(frozen=True)
class AtomicCylinder(Atom):
    atom_type: ClassVar[str] = "Cylinder"

    plane: AtomicPlane = None  # type: ignore[assignment]
    radius: float = 1.0
    height: float = 1.0

    def __post_init__(self):
        if self.plane is None:
            object.__setattr__(self, "plane", AtomicPlane.world_xy())

    def to_json(self) -> dict:
        return {
            "type": "Cylinder",
            "plane": self.plane.to_json(),
            "radius": self.radius,
            "height": self.height,
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicCylinder:
        return cls(
            plane=AtomicPlane.from_json(data["plane"]),
            radius=data["radius"],
            height=data["height"],
        )

