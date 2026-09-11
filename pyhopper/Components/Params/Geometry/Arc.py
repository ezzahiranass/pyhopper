"""Arc - Contains a collection of circular arcs (Grasshopper "Circular Arc")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicArc
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Arc(Component):
    """Contains a collection of circular arcs.

    Inputs:
        arc: Arc atoms to contain (Grasshopper Circular Arc).

    Outputs:
        arc: The same arcs (Grasshopper Circular Arc).

    Notes:
        Grasshopper: Params > Geometry > Circular Arc (Arc).
        pyhopper decisions: containers are components with one input and one output of the same
        name, like ``Circle``; the class is named after the atom.
    """

    display_name = "Circular Arc"
    nickname = "Arc"
    gh_guid = "04d3eace-deaa-475e-9e69-8f804d687998"

    inputs = [InputParam("arc", AtomicArc, Access.ITEM)]
    outputs = [OutputParam("arc", AtomicArc)]

    def generate(self, arc=None):
        return arc
