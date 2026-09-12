"""Serial plane alignment shared by Align Planes."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane
from pyhopper.Utils.Vectors import cross, dot, is_zero, scale, sub


def _project(vector, normal):
    return sub(vector, scale(normal, dot(vector, normal)))


def align_to(plane: AtomicPlane, reference: AtomicPlane) -> AtomicPlane:
    """Rotate ``plane`` about its normal so its x axis follows ``reference``'s x axis projected onto it;
    when that projection vanishes match the y axes instead (Grasshopper-verified)."""
    x_axis = _project(reference.x_axis, plane.normal)
    if not is_zero(x_axis, 1e-9):
        return AtomicPlane(plane.origin, plane.normal, x_axis)
    y_axis = _project(reference.y_axis, plane.normal)
    if is_zero(y_axis, 1e-9):
        return plane
    return AtomicPlane(plane.origin, plane.normal, cross(y_axis, plane.normal))
