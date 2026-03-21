"""Transform application utilities for pyhopper geometry atoms."""

from __future__ import annotations

from pyhopper.Core.Atoms import (
    Atom,
    AtomicArc,
    AtomicBrep,
    AtomicCircle,
    AtomicCylinder,
    AtomicLine,
    AtomicMesh,
    AtomicNurbsCurve,
    AtomicPlane,
    AtomicPoint,
    AtomicPolyline,
    AtomicSurface,
    AtomicTransform,
    AtomicVector,
)


def _transform_point(m: tuple[float, ...], p: AtomicPoint) -> AtomicPoint:
    """Apply a 4x4 row-major matrix to a point (w=1)."""
    x = m[0] * p.x + m[1] * p.y + m[2] * p.z + m[3]
    y = m[4] * p.x + m[5] * p.y + m[6] * p.z + m[7]
    z = m[8] * p.x + m[9] * p.y + m[10] * p.z + m[11]
    return AtomicPoint(x, y, z)


def _transform_vector(m: tuple[float, ...], v: AtomicVector) -> AtomicVector:
    """Apply the 3x3 sub-matrix to a direction vector (no translation)."""
    x = m[0] * v.x + m[1] * v.y + m[2] * v.z
    y = m[4] * v.x + m[5] * v.y + m[6] * v.z
    z = m[8] * v.x + m[9] * v.y + m[10] * v.z
    return AtomicVector(x, y, z)


def _transform_plane(m: tuple[float, ...], plane: AtomicPlane) -> AtomicPlane:
    return AtomicPlane(
        origin=_transform_point(m, plane.origin),
        normal=_transform_vector(m, plane.normal).unitize(),
        x_axis=_transform_vector(m, plane.x_axis).unitize(),
    )


def apply_transform(transform: AtomicTransform, atom: Atom) -> Atom:
    """Apply a transform to any supported geometry atom.

    Returns a new atom of the same type with transformed coordinates.
    Raises ``TypeError`` for unsupported atom types.
    """
    m = transform.matrix

    if isinstance(atom, AtomicPoint):
        return _transform_point(m, atom)

    if isinstance(atom, AtomicVector):
        return _transform_vector(m, atom)

    if isinstance(atom, AtomicPlane):
        return _transform_plane(m, atom)

    if isinstance(atom, AtomicLine):
        return AtomicLine(
            start=_transform_point(m, atom.start),
            end=_transform_point(m, atom.end),
        )

    if isinstance(atom, AtomicCircle):
        return AtomicCircle(
            plane=_transform_plane(m, atom.plane),
            radius=atom.radius,
        )

    if isinstance(atom, AtomicArc):
        return AtomicArc(
            plane=_transform_plane(m, atom.plane),
            radius=atom.radius,
            angle=atom.angle,
        )

    if isinstance(atom, AtomicPolyline):
        return AtomicPolyline(
            points=tuple(_transform_point(m, p) for p in atom.points),
        )

    if isinstance(atom, AtomicNurbsCurve):
        return AtomicNurbsCurve(
            control_points=tuple(_transform_point(m, p) for p in atom.control_points),
            weights=atom.weights,
            knots=atom.knots,
            degree=atom.degree,
        )

    if isinstance(atom, AtomicSurface):
        return AtomicSurface(
            poles=tuple(
                tuple(_transform_point(m, p) for p in row)
                for row in atom.poles
            ),
            weights=atom.weights,
            u_knots=atom.u_knots,
            v_knots=atom.v_knots,
            u_mults=atom.u_mults,
            v_mults=atom.v_mults,
            u_degree=atom.u_degree,
            v_degree=atom.v_degree,
            u_periodic=atom.u_periodic,
            v_periodic=atom.v_periodic,
        )

    if isinstance(atom, AtomicMesh):
        return AtomicMesh(
            vertices=tuple(_transform_point(m, v) for v in atom.vertices),
            faces=atom.faces,
        )

    if isinstance(atom, AtomicBrep):
        return AtomicBrep(
            faces=tuple(apply_transform(transform, f) for f in atom.faces),
        )

    if isinstance(atom, AtomicCylinder):
        return AtomicCylinder(
            plane=_transform_plane(m, atom.plane),
            radius=atom.radius,
            height=atom.height,
        )

    raise TypeError(f"apply_transform does not support {type(atom).__name__}")
