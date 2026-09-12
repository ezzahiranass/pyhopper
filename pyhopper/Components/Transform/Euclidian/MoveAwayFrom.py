"""MoveAwayFrom - Translate (move) an object away from another object (Grasshopper "Move Away From")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform

from .._geometry import move_away_translation
from pyhopper.Core.TypeSystem import GEOMETRY


class MoveAwayFrom(Component):
    """Translate (move) an object away from another object.

    Inputs:
        geometry: Geometry to move (Grasshopper Geometry [item]).
        emitter: Geometry to move away from (Grasshopper Emitter [item]).
        distance: Distance to move (negative values move towards) (Grasshopper Distance [item]).

    Outputs:
        geometry: Translated geometry (Grasshopper Geometry).
        transform: Transformation data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Euclidean > Move Away From (MoveAway).
        pyhopper decisions: Grasshopper-verified — the geometry moves ``distance`` along the line from
        the emitter's closest point to the geometry's reference point (its bounding-box centre) to that
        point; emitters are measured exactly for points, lines, polylines, rectangles, circles, boxes and
        planes (a plane counts as the square [-1, 1]² on it, as in Grasshopper), other atoms by their
        bounding-box centre until the closest-point kernel lands. Coincident objects do not move; a
        negative distance moves towards the emitter. Default distance 10.
    """

    display_name = "Move Away From"
    nickname = "MoveAway"
    gh_guid = "dd9f597a-4db0-42b1-9cb2-5607ec97db09"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM),
        InputParam("emitter", GEOMETRY, Access.ITEM),
        InputParam("distance", float, Access.ITEM, default=10.0),
    ]
    outputs = [
        OutputParam("geometry", GEOMETRY),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, emitter=None, distance=10.0):
        xform = AtomicTransform.translation(move_away_translation(geometry, emitter, float(distance)))
        return apply_transform(xform, geometry), xform
