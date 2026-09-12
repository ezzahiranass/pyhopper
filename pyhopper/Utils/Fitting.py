"""Least-squares fitting in pure Python (no numpy).

The 3x3 symmetric eigen-decomposition is a cyclic Jacobi iteration — more than
enough for the covariance matrices the fitting components build.
"""

from __future__ import annotations

import math
from typing import Sequence

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicVector
from pyhopper.Utils.Vectors import perpendicular

Matrix3 = list[list[float]]


def jacobi_eigen_symmetric(matrix: Matrix3, sweeps: int = 50) -> tuple[list[float], Matrix3]:
    """Eigenvalues and eigenvectors (as columns) of a symmetric 3x3 matrix."""
    a = [row[:] for row in matrix]
    v: Matrix3 = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    for _ in range(sweeps):
        off = sum(a[i][j] ** 2 for i in range(3) for j in range(3) if i != j)
        if off < 1e-30:
            break
        for p in range(3):
            for q in range(p + 1, 3):
                if abs(a[p][q]) < 1e-300:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = math.copysign(1.0, theta) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(3):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
                for k in range(3):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
                for k in range(3):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p], v[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    return [a[0][0], a[1][1], a[2][2]], v


def fit_plane(points: Sequence[AtomicPoint]) -> tuple[AtomicPlane, float]:
    """Least-squares plane through ``points`` and the largest point deviation.

    The normal is the covariance eigenvector of smallest eigenvalue, oriented
    towards +Z (then +Y, then +X) so results are reproducible; the X axis follows
    Rhino's ``PerpendicularTo`` rule and the origin is the world origin projected
    onto the plane — both as Grasshopper's Plane Fit reports them. Fewer than
    three points, or points that are all collinear, raise ``ValueError``.
    """
    if len(points) < 3:
        raise ValueError("Plane fitting needs at least three points")
    count = len(points)
    cx = sum(p.x for p in points) / count
    cy = sum(p.y for p in points) / count
    cz = sum(p.z for p in points) / count
    cov: Matrix3 = [[0.0] * 3 for _ in range(3)]
    for p in points:
        d = (p.x - cx, p.y - cy, p.z - cz)
        for i in range(3):
            for j in range(3):
                cov[i][j] += d[i] * d[j]
    values, vectors = jacobi_eigen_symmetric(cov)
    order = sorted(range(3), key=lambda index: values[index])
    smallest, middle = order[0], order[1]
    scale = max(abs(value) for value in values) or 1.0
    if values[middle] / scale < 1e-12:
        raise ValueError("Plane fitting needs points that are not all collinear")
    nx, ny, nz = (vectors[k][smallest] for k in range(3))
    if nz < 0 or (nz == 0 and (ny < 0 or (ny == 0 and nx < 0))):
        nx, ny, nz = -nx, -ny, -nz
    normal = AtomicVector(nx, ny, nz).unitize()
    # origin: the world origin projected onto the plane through the centroid
    offset = normal.x * cx + normal.y * cy + normal.z * cz
    origin = AtomicPoint(normal.x * offset, normal.y * offset, normal.z * offset)
    plane = AtomicPlane(origin, normal, perpendicular(normal))
    deviation = max(abs((p.x - cx) * normal.x + (p.y - cy) * normal.y + (p.z - cz) * normal.z) for p in points)
    return plane, deviation
