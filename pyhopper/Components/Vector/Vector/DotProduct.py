"""DotProduct - Compute the dot product of two vectors."""

from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class DotProduct(Component):
    """Compute the dot product of two vectors.

    When ``unitize`` is true, both vectors are unitized before the dot product
    is evaluated.
    """

    inputs = [
        InputParam("vector_a", AtomicVector, Access.ITEM),
        InputParam("vector_b", AtomicVector, Access.ITEM),
        InputParam("unitize", bool, Access.ITEM, default=False),
    ]
    outputs = [OutputParam("dot_product", float)]

    def generate(self, vector_a=None, vector_b=None, unitize=False):
        if unitize:
            vector_a = vector_a.unitize()
            vector_b = vector_b.unitize()
        return vector_a.x * vector_b.x + vector_a.y * vector_b.y + vector_a.z * vector_b.z
