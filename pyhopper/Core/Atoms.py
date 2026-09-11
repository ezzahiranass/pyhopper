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


def atom_from_json(data: dict) -> Atom:
    """Deserialize one registered atom from its JSON representation."""
    atom_type = data.get("type")
    atom_cls = ATOM_REGISTRY.get(atom_type)
    if atom_cls is None:
        raise ValueError(f"Unknown atom type: {atom_type!r}")
    return atom_cls.from_json(data)


def _open_uniform_bspline_data(point_count: int, degree: int) -> tuple[tuple[float, ...], tuple[int, ...], int]:
    if point_count < 2:
        raise ValueError("A spline requires at least two control points")

    clamped_degree = max(1, min(int(degree), point_count - 1))
    knot_count = point_count - clamped_degree + 1

    if knot_count == 2:
        knots = (0.0, 1.0)
        mults = (clamped_degree + 1, clamped_degree + 1)
        return knots, mults, clamped_degree

    denominator = float(knot_count - 1)
    knots = tuple(index / denominator for index in range(knot_count))
    mults = tuple(
        clamped_degree + 1 if index in (0, knot_count - 1) else 1
        for index in range(knot_count)
    )
    return knots, mults, clamped_degree


def _collapse_repeated_knots(knots: tuple[float, ...]) -> tuple[tuple[float, ...], tuple[int, ...]]:
    if not knots:
        return (), ()

    unique_knots = [knots[0]]
    multiplicities = [1]

    for knot in knots[1:]:
        if knot == unique_knots[-1]:
            multiplicities[-1] += 1
        else:
            unique_knots.append(knot)
            multiplicities.append(1)

    return tuple(unique_knots), tuple(multiplicities)


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
    """Rhino-style orthonormal plane defined by origin, normal, and X axis.

    The Y axis is derived as ``normal x x_axis``. Input axes are normalized
    and the X axis is projected onto the plane during construction.
    """

    atom_type: ClassVar[str] = "Plane"

    origin: AtomicPoint = None  # type: ignore[assignment]
    normal: AtomicVector = None  # type: ignore[assignment]
    x_axis: AtomicVector = None  # type: ignore[assignment]

    def __post_init__(self):
        origin = self.origin if self.origin is not None else AtomicPoint.origin()
        normal = self.normal if self.normal is not None else AtomicVector.unit_z()
        x_axis = self.x_axis if self.x_axis is not None else AtomicVector.unit_x()

        normal = normal.unitize()
        if normal.length == 0.0:
            raise ValueError("AtomicPlane normal must be non-zero")

        projection = x_axis.x * normal.x + x_axis.y * normal.y + x_axis.z * normal.z
        x_axis = AtomicVector(
            x_axis.x - projection * normal.x,
            x_axis.y - projection * normal.y,
            x_axis.z - projection * normal.z,
        ).unitize()
        if x_axis.length == 0.0:
            raise ValueError("AtomicPlane x axis must not be parallel to its normal")

        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "normal", normal)
        object.__setattr__(self, "x_axis", x_axis)

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
    def world_xy(cls, origin: AtomicPoint | None = None) -> AtomicPlane:
        return cls(origin or AtomicPoint.origin(), AtomicVector.unit_z(), AtomicVector.unit_x())

    @classmethod
    def world_xz(cls, origin: AtomicPoint | None = None) -> AtomicPlane:
        return cls(origin or AtomicPoint.origin(), AtomicVector(0.0, -1.0, 0.0), AtomicVector.unit_x())

    @classmethod
    def world_yz(cls, origin: AtomicPoint | None = None) -> AtomicPlane:
        return cls(origin or AtomicPoint.origin(), AtomicVector.unit_x(), AtomicVector.unit_y())


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
class AtomicEllipse(Atom):
    """Named ellipse defined by a plane and two radii."""

    atom_type: ClassVar[str] = "Ellipse"

    plane: AtomicPlane = None  # type: ignore[assignment]
    radius_x: float = 1.0
    radius_y: float = 0.5

    def __post_init__(self):
        if self.plane is None:
            object.__setattr__(self, "plane", AtomicPlane.world_xy())

    def to_json(self) -> dict:
        return {
            "type": "Ellipse",
            "plane": self.plane.to_json(),
            "radius_x": self.radius_x,
            "radius_y": self.radius_y,
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicEllipse:
        return cls(
            plane=AtomicPlane.from_json(data["plane"]),
            radius_x=data["radius_x"],
            radius_y=data["radius_y"],
        )


@dataclass(frozen=True)
class AtomicRectangle(Atom):
    """Named rectangle defined by a centered plane and side lengths."""

    atom_type: ClassVar[str] = "Rectangle"

    plane: AtomicPlane = None  # type: ignore[assignment]
    x_size: float = 1.0
    y_size: float = 1.0

    def __post_init__(self):
        if self.plane is None:
            object.__setattr__(self, "plane", AtomicPlane.world_xy())

    def to_json(self) -> dict:
        return {
            "type": "Rectangle",
            "plane": self.plane.to_json(),
            "x_size": self.x_size,
            "y_size": self.y_size,
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicRectangle:
        return cls(
            plane=AtomicPlane.from_json(data["plane"]),
            x_size=data["x_size"],
            y_size=data["y_size"],
        )


@dataclass(frozen=True)
class AtomicBox(Atom):
    """Named box defined by a centered plane and three side lengths."""

    atom_type: ClassVar[str] = "Box"

    plane: AtomicPlane = None  # type: ignore[assignment]
    x_size: float = 1.0
    y_size: float = 1.0
    z_size: float = 1.0

    def __post_init__(self):
        if self.plane is None:
            object.__setattr__(self, "plane", AtomicPlane.world_xy())

    def to_json(self) -> dict:
        return {
            "type": "Box",
            "plane": self.plane.to_json(),
            "x_size": self.x_size,
            "y_size": self.y_size,
            "z_size": self.z_size,
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicBox:
        return cls(
            plane=AtomicPlane.from_json(data["plane"]),
            x_size=data["x_size"],
            y_size=data["y_size"],
            z_size=data["z_size"],
        )


@dataclass(frozen=True)
class AtomicInterpolatedCurve(Atom):
    """Curve that passes through each interpolation point."""

    atom_type: ClassVar[str] = "InterpolatedCurve"

    points: tuple[AtomicPoint, ...] = ()
    degree: int = 3

    def to_json(self) -> dict:
        return {
            "type": "InterpolatedCurve",
            "points": [point.to_json() for point in self.points],
            "degree": self.degree,
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicInterpolatedCurve:
        return cls(
            points=tuple(AtomicPoint.from_json(point) for point in data["points"]),
            degree=data.get("degree", 3),
        )


@dataclass(frozen=True)
class AtomicControlPointCurve(Atom):
    """Clamped NURBS curve defined directly by its control points."""

    atom_type: ClassVar[str] = "ControlPointCurve"

    control_points: tuple[AtomicPoint, ...] = ()
    degree: int = 3

    def to_json(self) -> dict:
        return {
            "type": "ControlPointCurve",
            "control_points": [point.to_json() for point in self.control_points],
            "degree": self.degree,
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicControlPointCurve:
        return cls(
            control_points=tuple(
                AtomicPoint.from_json(point) for point in data["control_points"]
            ),
            degree=data.get("degree", 3),
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
    """Tensor-product B-spline surface representation."""

    atom_type: ClassVar[str] = "Surface"

    poles: tuple[tuple[AtomicPoint, ...], ...] = ()
    weights: tuple[tuple[float, ...], ...] = ()
    u_knots: tuple[float, ...] = ()
    v_knots: tuple[float, ...] = ()
    u_mults: tuple[int, ...] = ()
    v_mults: tuple[int, ...] = ()
    u_degree: int = 3
    v_degree: int = 3
    u_periodic: bool = False
    v_periodic: bool = False

    def __post_init__(self):
        if not self.poles:
            return

        row_lengths = {len(row) for row in self.poles}
        if len(row_lengths) != 1 or 0 in row_lengths:
            raise ValueError("AtomicSurface poles must form a rectangular non-empty grid")

        v_count = len(self.poles)
        u_count = len(self.poles[0])

        if self.weights:
            if len(self.weights) != v_count or any(len(row) != u_count for row in self.weights):
                raise ValueError("AtomicSurface weights must match the poles grid dimensions")
        else:
            object.__setattr__(
                self,
                "weights",
                tuple(tuple(1.0 for _ in range(u_count)) for _ in range(v_count)),
            )

        if not self.u_knots or not self.u_mults:
            u_knots, u_mults, u_degree = _open_uniform_bspline_data(u_count, self.u_degree)
            object.__setattr__(self, "u_knots", u_knots)
            object.__setattr__(self, "u_mults", u_mults)
            object.__setattr__(self, "u_degree", u_degree)

        if not self.v_knots or not self.v_mults:
            v_knots, v_mults, v_degree = _open_uniform_bspline_data(v_count, self.v_degree)
            object.__setattr__(self, "v_knots", v_knots)
            object.__setattr__(self, "v_mults", v_mults)
            object.__setattr__(self, "v_degree", v_degree)

    def to_json(self) -> dict:
        return {
            "type": "Surface",
            "poles": [
                [p.to_json() for p in row] for row in self.poles
            ],
            "weights": [list(row) for row in self.weights],
            "u_knots": list(self.u_knots),
            "v_knots": list(self.v_knots),
            "u_mults": list(self.u_mults),
            "v_mults": list(self.v_mults),
            "u_degree": self.u_degree,
            "v_degree": self.v_degree,
            "u_periodic": self.u_periodic,
            "v_periodic": self.v_periodic,
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicSurface:
        if "poles" not in data:
            legacy_poles = tuple(
                tuple(AtomicPoint.from_json(point) for point in row)
                for row in data.get("control_points", [])
            )
            v_count = len(legacy_poles)
            u_count = len(legacy_poles[0]) if legacy_poles else 0
            weights = tuple(tuple(1.0 for _ in range(u_count)) for _ in range(v_count))
            u_knots, u_mults, u_degree = _open_uniform_bspline_data(u_count, data.get("degree_u", 3)) if u_count >= 2 else ((), (), data.get("degree_u", 3))
            v_knots, v_mults, v_degree = _open_uniform_bspline_data(v_count, data.get("degree_v", 3)) if v_count >= 2 else ((), (), data.get("degree_v", 3))
            return cls(
                poles=legacy_poles,
                weights=weights,
                u_knots=u_knots,
                v_knots=v_knots,
                u_mults=u_mults,
                v_mults=v_mults,
                u_degree=u_degree,
                v_degree=v_degree,
            )

        return cls(
            poles=tuple(
                tuple(AtomicPoint.from_json(p) for p in row)
                for row in data["poles"]
            ),
            weights=tuple(tuple(float(weight) for weight in row) for row in data.get("weights", [])),
            u_knots=tuple(float(knot) for knot in data.get("u_knots", ())),
            v_knots=tuple(float(knot) for knot in data.get("v_knots", ())),
            u_mults=tuple(int(mult) for mult in data.get("u_mults", ())),
            v_mults=tuple(int(mult) for mult in data.get("v_mults", ())),
            u_degree=data["u_degree"],
            v_degree=data["v_degree"],
            u_periodic=bool(data.get("u_periodic", False)),
            v_periodic=bool(data.get("v_periodic", False)),
        )


@dataclass(frozen=True)
class AtomicTrimmedSurface(Atom):
    """Surface patch with UV-space trim loops.

    ``surface`` stores the underlying untrimmed tensor-product surface.
    ``outer`` and ``holes`` are closed ``AtomicPolyline`` loops in the
    surface's parameter space, where point ``x`` is U and point ``y`` is V.
    """

    atom_type: ClassVar[str] = "TrimmedSurface"

    surface: AtomicSurface = None  # type: ignore[assignment]
    outer: AtomicPolyline = None  # type: ignore[assignment]
    holes: tuple[AtomicPolyline, ...] = ()

    def __post_init__(self):
        if self.surface is None:
            raise ValueError("AtomicTrimmedSurface requires a base surface")
        if not isinstance(self.surface, AtomicSurface):
            raise TypeError("AtomicTrimmedSurface surface must be an AtomicSurface")
        if self.outer is None:
            raise ValueError("AtomicTrimmedSurface requires an outer trim loop")
        if not isinstance(self.outer, AtomicPolyline):
            raise TypeError("AtomicTrimmedSurface outer trim must be an AtomicPolyline")
        for index, hole in enumerate(self.holes):
            if not isinstance(hole, AtomicPolyline):
                raise TypeError(f"AtomicTrimmedSurface hole {index} must be an AtomicPolyline")

    def to_json(self) -> dict:
        return {
            "type": "TrimmedSurface",
            "surface": self.surface.to_json(),
            "outer": self.outer.to_json(),
            "holes": [hole.to_json() for hole in self.holes],
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicTrimmedSurface:
        return cls(
            surface=AtomicSurface.from_json(data["surface"]),
            outer=AtomicPolyline.from_json(data["outer"]),
            holes=tuple(AtomicPolyline.from_json(hole) for hole in data.get("holes", [])),
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


@dataclass(frozen=True)
class AtomicBrep(Atom):
    """Boundary representation solid.

    A Brep is defined by a closed shell of oriented surface faces.  Each face
    is an ``AtomicSurface`` whose normal is assumed to point outward.  The
    tuple of faces is ordered: by convention the outer shell comes first.

    Current scope (exact NURBS, no external deps):
      - ``faces``  — the untrimmed surface patches that bound the solid.

    Future extensions (when build123d / OCCT is available):
      - Per-face 2-D trim curves (``AtomicNurbsCurve`` in parameter space).
      - Explicit edge topology (shared edge references between faces).
      - Inner shells for cavities / voids.

    These fields are reserved but not yet present.  Adding them later will
    not break existing Brep atoms because the serialisation format is
    forward-compatible (unknown keys are ignored on ``from_json``).
    """

    atom_type: ClassVar[str] = "Brep"

    faces: tuple[AtomicSurface | AtomicTrimmedSurface, ...] = ()

    def __post_init__(self):
        if not self.faces:
            return
        for i, face in enumerate(self.faces):
            if not isinstance(face, (AtomicSurface, AtomicTrimmedSurface)):
                raise TypeError(
                    f"AtomicBrep face {i} must be an AtomicSurface or AtomicTrimmedSurface, "
                    f"got {type(face).__name__}"
                )

    @property
    def face_count(self) -> int:
        return len(self.faces)

    def to_json(self) -> dict:
        return {
            "type": "Brep",
            "faces": [f.to_json() for f in self.faces],
        }

    @classmethod
    def from_json(cls, data: dict) -> AtomicBrep:
        return cls(
            faces=tuple(atom_from_json(f) for f in data.get("faces", [])),
        )


# ── Identity matrix constant ──────────────────────────────────────

_IDENTITY_4X4 = (
    1.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0,
)


@dataclass(frozen=True)
class AtomicTransform(Atom):
    """4x4 affine transformation matrix (row-major)."""

    atom_type: ClassVar[str] = "Transform"

    matrix: tuple[float, ...] = _IDENTITY_4X4

    @classmethod
    def identity(cls) -> AtomicTransform:
        return cls()

    @classmethod
    def translation(cls, vector: AtomicVector) -> AtomicTransform:
        return cls(matrix=(
            1.0, 0.0, 0.0, vector.x,
            0.0, 1.0, 0.0, vector.y,
            0.0, 0.0, 1.0, vector.z,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def scale(cls, center: AtomicPoint, factor: float) -> AtomicTransform:
        """Uniform scale around *center*."""
        value = float(factor)
        return cls(matrix=(
            value, 0.0,   0.0,   center.x * (1.0 - value),
            0.0,   value, 0.0,   center.y * (1.0 - value),
            0.0,   0.0,   value, center.z * (1.0 - value),
            0.0,   0.0,   0.0,   1.0,
        ))

    @classmethod
    def scale_non_uniform(
        cls,
        plane: AtomicPlane,
        x_factor: float,
        y_factor: float,
        z_factor: float,
    ) -> AtomicTransform:
        """Non-uniform scale in a plane's local coordinate system."""
        x = plane.x_axis
        y = plane.y_axis
        z = plane.normal
        factors = (float(x_factor), float(y_factor), float(z_factor))
        axes = (x, y, z)
        coordinates = ("x", "y", "z")
        linear = [
            [
                sum(
                    factors[k] * getattr(axes[k], coordinates[row]) * getattr(axes[k], coordinates[col])
                    for k in range(3)
                )
                for col in range(3)
            ]
            for row in range(3)
        ]
        origin = plane.origin
        translation = (
            origin.x - sum(linear[0][index] * (origin.x, origin.y, origin.z)[index] for index in range(3)),
            origin.y - sum(linear[1][index] * (origin.x, origin.y, origin.z)[index] for index in range(3)),
            origin.z - sum(linear[2][index] * (origin.x, origin.y, origin.z)[index] for index in range(3)),
        )
        return cls(matrix=(
            linear[0][0], linear[0][1], linear[0][2], translation[0],
            linear[1][0], linear[1][1], linear[1][2], translation[1],
            linear[2][0], linear[2][1], linear[2][2], translation[2],
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def orient(cls, source: AtomicPlane, target: AtomicPlane) -> AtomicTransform:
        """Change basis from *source* plane coordinates to *target* plane coordinates."""
        source_axes = (source.x_axis, source.y_axis, source.normal)
        target_axes = (target.x_axis, target.y_axis, target.normal)
        coordinates = ("x", "y", "z")
        linear = [
            [
                sum(
                    getattr(target_axes[k], coordinates[row]) * getattr(source_axes[k], coordinates[col])
                    for k in range(3)
                )
                for col in range(3)
            ]
            for row in range(3)
        ]
        source_origin = (source.origin.x, source.origin.y, source.origin.z)
        target_origin = (target.origin.x, target.origin.y, target.origin.z)
        translation = tuple(
            target_origin[row] - sum(linear[row][col] * source_origin[col] for col in range(3))
            for row in range(3)
        )
        return cls(matrix=(
            linear[0][0], linear[0][1], linear[0][2], translation[0],
            linear[1][0], linear[1][1], linear[1][2], translation[1],
            linear[2][0], linear[2][1], linear[2][2], translation[2],
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def rotation(cls, origin: AtomicPoint, axis: AtomicVector, angle: float) -> AtomicTransform:
        """Rotation around *axis* through *origin* by *angle* radians."""
        n = axis.unitize()
        c = math.cos(angle)
        s = math.sin(angle)
        t = 1.0 - c
        nx, ny, nz = n.x, n.y, n.z

        # Rotation sub-matrix (Rodrigues)
        r00 = c + nx * nx * t
        r01 = nx * ny * t - nz * s
        r02 = nx * nz * t + ny * s
        r10 = ny * nx * t + nz * s
        r11 = c + ny * ny * t
        r12 = ny * nz * t - nx * s
        r20 = nz * nx * t - ny * s
        r21 = nz * ny * t + nx * s
        r22 = c + nz * nz * t

        # Translation: T(origin) * R * T(-origin)
        ox, oy, oz = origin.x, origin.y, origin.z
        tx = ox - r00 * ox - r01 * oy - r02 * oz
        ty = oy - r10 * ox - r11 * oy - r12 * oz
        tz = oz - r20 * ox - r21 * oy - r22 * oz

        return cls(matrix=(
            r00, r01, r02, tx,
            r10, r11, r12, ty,
            r20, r21, r22, tz,
            0.0, 0.0, 0.0, 1.0,
        ))

    @classmethod
    def reflection(cls, plane: AtomicPlane) -> AtomicTransform:
        """Reflection across *plane*."""
        n = plane.normal.unitize()
        a, b, c = n.x, n.y, n.z
        ox, oy, oz = plane.origin.x, plane.origin.y, plane.origin.z
        d = a * ox + b * oy + c * oz

        return cls(matrix=(
            1 - 2*a*a,  -2*a*b,    -2*a*c,    2*a*d,
            -2*b*a,     1 - 2*b*b, -2*b*c,    2*b*d,
            -2*c*a,     -2*c*b,    1 - 2*c*c, 2*c*d,
            0.0,        0.0,       0.0,       1.0,
        ))

    def to_json(self) -> dict:
        return {"type": "Transform", "matrix": list(self.matrix)}

    @classmethod
    def from_json(cls, data: dict) -> AtomicTransform:
        return cls(matrix=tuple(float(v) for v in data["matrix"]))
