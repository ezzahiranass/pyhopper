"""Transform application utilities for pyhopper geometry atoms."""

from __future__ import annotations

import math

from pyhopper.Core.Atoms import (
    Atom,
    AtomicBox,
    AtomicArc,
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
    AtomicTransform,
    AtomicVector,
)
from pyhopper.Core.DataTree import DataTree


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
    transformed_x = _transform_vector(m, plane.x_axis)
    transformed_y = _transform_vector(m, plane.y_axis)
    normal = AtomicVector(
        transformed_x.y * transformed_y.z - transformed_x.z * transformed_y.y,
        transformed_x.z * transformed_y.x - transformed_x.x * transformed_y.z,
        transformed_x.x * transformed_y.y - transformed_x.y * transformed_y.x,
    )
    return AtomicPlane(
        origin=_transform_point(m, plane.origin),
        normal=normal,
        x_axis=transformed_x,
    )


def _uniform_scale(m: tuple[float, ...]) -> float | None:
    columns = (
        (m[0], m[4], m[8]),
        (m[1], m[5], m[9]),
        (m[2], m[6], m[10]),
    )
    lengths = tuple(math.sqrt(sum(value * value for value in column)) for column in columns)
    if min(lengths) < 1e-12 or max(lengths) - min(lengths) > 1e-9 * max(lengths):
        return None
    for left in range(3):
        for right in range(left + 1, 3):
            dot = sum(columns[left][index] * columns[right][index] for index in range(3))
            if abs(dot) > 1e-9 * lengths[left] * lengths[right]:
                return None
    return sum(lengths) / 3.0


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
        uniform_scale = _uniform_scale(m)
        if uniform_scale is not None:
            return AtomicCircle(
                plane=_transform_plane(m, atom.plane),
                radius=atom.radius * uniform_scale,
            )
        from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

        return apply_transform(transform, as_nurbs_curve(atom))

    if isinstance(atom, AtomicArc):
        uniform_scale = _uniform_scale(m)
        if uniform_scale is not None:
            return AtomicArc(
                plane=_transform_plane(m, atom.plane),
                radius=atom.radius * uniform_scale,
                angle=atom.angle,
            )
        from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

        return apply_transform(transform, as_nurbs_curve(atom))

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

    if isinstance(atom, AtomicInterpolatedCurve):
        return AtomicInterpolatedCurve(
            points=tuple(_transform_point(m, point) for point in atom.points),
            degree=atom.degree,
        )

    if isinstance(atom, AtomicControlPointCurve):
        return AtomicControlPointCurve(
            control_points=tuple(_transform_point(m, point) for point in atom.control_points),
            degree=atom.degree,
        )

    if isinstance(atom, (AtomicEllipse, AtomicRectangle)):
        uniform_scale = _uniform_scale(m)
        if uniform_scale is None:
            from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve

            return apply_transform(transform, as_nurbs_curve(atom))
        if isinstance(atom, AtomicEllipse):
            return AtomicEllipse(
                plane=_transform_plane(m, atom.plane),
                radius_x=atom.radius_x * uniform_scale,
                radius_y=atom.radius_y * uniform_scale,
            )
        return AtomicRectangle(
            plane=_transform_plane(m, atom.plane),
            x_size=atom.x_size * uniform_scale,
            y_size=atom.y_size * uniform_scale,
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

    if isinstance(atom, AtomicBox):
        uniform_scale = _uniform_scale(m)
        if uniform_scale is None:
            from pyhopper.Utils.Boxes import box_to_brep

            return apply_transform(transform, box_to_brep(atom))
        return AtomicBox(
            plane=_transform_plane(m, atom.plane),
            x_size=atom.x_size * uniform_scale,
            y_size=atom.y_size * uniform_scale,
            z_size=atom.z_size * uniform_scale,
        )

    if isinstance(atom, AtomicCylinder):
        uniform_scale = _uniform_scale(m)
        if uniform_scale is None:
            linear_values = (m[0], m[1], m[2], m[4], m[5], m[6], m[8], m[9], m[10])
            if max(abs(value) for value in linear_values) < 1e-12:
                return AtomicCylinder(
                    plane=AtomicPlane(
                        origin=_transform_point(m, atom.plane.origin),
                        normal=atom.plane.normal,
                        x_axis=atom.plane.x_axis,
                    ),
                    radius=0.0,
                    height=0.0,
                )
            raise TypeError("AtomicCylinder only supports rigid and uniform-scale transforms")
        return AtomicCylinder(
            plane=_transform_plane(m, atom.plane),
            radius=atom.radius * uniform_scale,
            height=atom.height * uniform_scale,
        )

    raise TypeError(f"apply_transform does not support {type(atom).__name__}")


def apply_transform_tree(transform: AtomicTransform, tree: DataTree) -> DataTree:
    """Apply an affine transform to every atom while preserving DataTree paths."""
    return DataTree.from_branches({
        path: [apply_transform(transform, item) for item in branch]
        for path, branch in tree.branches()
    })
