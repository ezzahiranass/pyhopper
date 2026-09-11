"""Central one-to-one type coercion rules for pyhopper data."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .Atoms import (
    Atom,
    AtomicArc,
    AtomicBox,
    AtomicBrep,
    AtomicCircle,
    AtomicControlPointCurve,
    AtomicCylinder,
    AtomicEllipse,
    AtomicInterpolatedCurve,
    AtomicLine,
    AtomicMesh,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicRectangle,
    AtomicSurface,
    AtomicTrimmedSurface,
)
from .DataTree import DataTree
from .Path import Path


@dataclass(frozen=True)
class TypeSpec:
    """Semantic type accepted by typed ports and parameter containers."""

    name: str
    accepted_types: tuple[type, ...]

    @property
    def __name__(self) -> str:
        return self.name


CURVE_TYPES = (
    AtomicLine,
    AtomicCircle,
    AtomicArc,
    AtomicPolyline,
    AtomicNurbsCurve,
    AtomicEllipse,
    AtomicRectangle,
    AtomicInterpolatedCurve,
    AtomicControlPointCurve,
)

GEOMETRY_TYPES = (
    AtomicPoint,
    AtomicLine,
    AtomicCircle,
    AtomicArc,
    AtomicPolyline,
    AtomicNurbsCurve,
    AtomicEllipse,
    AtomicRectangle,
    AtomicBox,
    AtomicInterpolatedCurve,
    AtomicControlPointCurve,
    AtomicSurface,
    AtomicTrimmedSurface,
    AtomicMesh,
    AtomicBrep,
    AtomicCylinder,
    AtomicPlane,
)

CURVE = TypeSpec("Curve", CURVE_TYPES)
GEOMETRY = TypeSpec("Geometry", GEOMETRY_TYPES)
SURFACE = TypeSpec("Surface", (AtomicSurface, AtomicTrimmedSurface))


class CoercionError(TypeError):
    """Raised when a value cannot be deterministically coerced to a target type."""

    def __init__(
        self,
        target: type | TypeSpec,
        value: Any,
        *,
        input_name: str | None = None,
        path: Path | None = None,
        index: int | None = None,
        reason: str | None = None,
    ) -> None:
        target_name = type_name(target)
        source_name = type(value).__name__
        location = ""
        if path is not None and index is not None:
            location = f" at path {path}, item {index}"
        prefix = f"Input '{input_name}' " if input_name else ""
        detail = f": {reason}" if reason else ""
        super().__init__(f"{prefix}could not coerce {source_name} to {target_name}{location}{detail}")
        self.target = target
        self.value = value
        self.input_name = input_name
        self.path = path
        self.index = index
        self.reason = reason


def type_name(target: type | TypeSpec | None) -> str | None:
    if target is None:
        return None
    return target.name if isinstance(target, TypeSpec) else getattr(target, "__name__", str(target))


def accepted_type_names(target: type | TypeSpec | None) -> list[str] | None:
    """Return declarative accepted source types for catalog and UI metadata."""
    if target is None:
        return None
    if isinstance(target, TypeSpec):
        return [item.__name__ for item in target.accepted_types]
    if target is float:
        return ["int", "float"]
    if target is int:
        return ["int", "float"]
    if target is AtomicPlane:
        return ["AtomicPlane", "AtomicPoint"]
    if target is AtomicBrep:
        return ["AtomicBrep", "AtomicBox", "AtomicSurface", "AtomicTrimmedSurface"]
    if target is AtomicSurface:
        return ["AtomicSurface", "AtomicBrep"]
    return [target.__name__]


def _round_half_away_from_zero(value: float) -> int:
    magnitude = math.floor(abs(value) + 0.5)
    return magnitude if value >= 0.0 else -magnitude


def coerce_item(value: Any, target: type | TypeSpec | None) -> Any:
    """Coerce one value without changing item cardinality."""
    if target is None:
        return value

    if isinstance(target, TypeSpec):
        if isinstance(value, target.accepted_types):
            return value
        raise CoercionError(target, value)

    if target is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CoercionError(target, value)
        result = float(value)
        if not math.isfinite(result):
            raise CoercionError(target, value, reason="number must be finite")
        return result

    if target is int:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CoercionError(target, value)
        numeric = float(value)
        if not math.isfinite(numeric):
            raise CoercionError(target, value, reason="number must be finite")
        return _round_half_away_from_zero(numeric)

    if target is bool:
        if type(value) is bool:
            return value
        raise CoercionError(target, value)

    if target is str:
        if isinstance(value, str):
            return value
        raise CoercionError(target, value)

    if target is AtomicPlane and isinstance(value, AtomicPoint):
        return AtomicPlane.world_xy(value)

    if target is AtomicBrep:
        if isinstance(value, AtomicBox):
            from pyhopper.Utils.Boxes import box_to_brep

            return box_to_brep(value)
        if isinstance(value, AtomicSurface):
            return AtomicBrep(faces=(value,))
        if isinstance(value, AtomicTrimmedSurface):
            return AtomicBrep(faces=(value,))

    if target is AtomicSurface and isinstance(value, AtomicBrep):
        if value.face_count == 1:
            face = value.faces[0]
            if isinstance(face, AtomicSurface):
                return face
            raise CoercionError(
                target,
                value,
                reason="Brep face is trimmed; use a Surface-compatible port instead",
            )
        raise CoercionError(
            target,
            value,
            reason=f"Brep has {value.face_count} faces; surface extraction is ambiguous",
        )

    if isinstance(value, target):
        return value
    raise CoercionError(target, value)


def coerce_tree(
    tree: DataTree,
    target: type | TypeSpec | None,
    *,
    input_name: str | None = None,
) -> DataTree:
    """Coerce every item while preserving all DataTree paths and item counts."""
    branches = {}
    for path, branch in tree.branches():
        items = []
        for index, value in enumerate(branch):
            try:
                items.append(coerce_item(value, target))
            except CoercionError as exc:
                if exc.path is not None:
                    raise
                raise CoercionError(
                    target,
                    value,
                    input_name=input_name,
                    path=path,
                    index=index,
                    reason=exc.reason,
                ) from exc
        branches[path] = items
    return DataTree.from_branches(branches)
