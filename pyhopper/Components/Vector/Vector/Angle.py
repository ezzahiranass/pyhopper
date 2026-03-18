"""Angle - Compute the angle between two vectors."""

import math

from pyhopper.Core.Atoms import AtomicPlane, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _dot_product(a: AtomicVector, b: AtomicVector) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


def _project_onto_plane(vector: AtomicVector, plane: AtomicPlane) -> AtomicVector:
    normal = plane.normal.unitize()
    component = _dot_product(vector, normal)
    return AtomicVector(
        vector.x - normal.x * component,
        vector.y - normal.y * component,
        vector.z - normal.z * component,
    )


class Angle(Component):
    """Compute the angle and reflex angle between two vectors.

    When a plane is supplied, the vectors are projected to that plane before
    the angles are measured.
    """

    inputs = [
        InputParam("vector_a", AtomicVector, Access.ITEM),
        InputParam("vector_b", AtomicVector, Access.ITEM),
        InputParam("plane", AtomicPlane, Access.ITEM, default=None, optional=True),
    ]
    outputs = [
        OutputParam("angle", float),
        OutputParam("reflex", float),
    ]

    def generate(self, vector_a=None, vector_b=None, plane=None):
        if plane is not None:
            vector_a = _project_onto_plane(vector_a, plane)
            vector_b = _project_onto_plane(vector_b, plane)

        a = vector_a.unitize()
        b = vector_b.unitize()
        cosine = max(-1.0, min(1.0, _dot_product(a, b)))
        angle = math.acos(cosine)
        return angle, (2.0 * math.pi) - angle
