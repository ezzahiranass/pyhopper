"""BoxCorners - Extract all 8 corners of a box (Grasshopper "Box Corners")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBox, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Boxes import box_corners


class BoxCorners(Component):
    """Extract all 8 corners of a box.

    Inputs:
        box: Base box (Grasshopper Box [item]).

    Outputs:
        corner_a: Corner at {x=min, y=min, z=min} (Grasshopper Corner A).
        corner_b: Corner at {x=max, y=min, z=min} (Grasshopper Corner B).
        corner_c: Corner at {x=max, y=max, z=min} (Grasshopper Corner C).
        corner_d: Corner at {x=min, y=max, z=min} (Grasshopper Corner D).
        corner_e: Corner at {x=min, y=min, z=max} (Grasshopper Corner E).
        corner_f: Corner at {x=max, y=min, z=max} (Grasshopper Corner F).
        corner_g: Corner at {x=max, y=max, z=max} (Grasshopper Corner G).
        corner_h: Corner at {x=min, y=max, z=max} (Grasshopper Corner H).

    Notes:
        Grasshopper: Surface > Analysis > Box Corners (Box Corners).
        pyhopper decisions: none; corners A-D are the bottom face counter-clockwise from the (x-, y-) corner, E-H the top face above them, as in Grasshopper.
    """

    display_name = "Box Corners"
    nickname = "Box Corners"
    gh_guid = "a10e8cdf-7c7a-4aac-aa70-ddb7010ab231"

    inputs = [
        InputParam("box", AtomicBox, Access.ITEM),
    ]
    outputs = [
        OutputParam("corner_a", AtomicPoint),
        OutputParam("corner_b", AtomicPoint),
        OutputParam("corner_c", AtomicPoint),
        OutputParam("corner_d", AtomicPoint),
        OutputParam("corner_e", AtomicPoint),
        OutputParam("corner_f", AtomicPoint),
        OutputParam("corner_g", AtomicPoint),
        OutputParam("corner_h", AtomicPoint),
    ]

    def generate(self, box=None):
        return tuple(box_corners(box))
