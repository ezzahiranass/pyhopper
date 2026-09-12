"""PolygonCenter - Find the center point (average) for a polyline (Grasshopper "Polygon Center")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Polygons import polygon_centres
from pyhopper.Core.TypeSystem import CURVE


class PolygonCenter(Component):
    """Find the center point (average) for a polyline.

    Inputs:
        polyline: Polyline to average. (Grasshopper Polyline [item]).

    Outputs:
        center_v: Average of polyline vertices. (Grasshopper Center(V)).
        center_e: Average of polyline edges (Grasshopper Center(E)).
        center_a: Area centroid of polyline shape (Grasshopper Center(A)).

    Notes:
        Grasshopper: Curve > Analysis > Polygon Center (PCen).
        pyhopper decisions: vertex centre = mean of the distinct vertices, edge centre = edge midpoints weighted by
        edge length, area centre = area centroid (open polylines emit nothing there, Grasshopper
        emits a null); non-polyline curves raise ``TypeError``.
    """

    display_name = "Polygon Center"
    nickname = "PCen"
    gh_guid = "59e94548-cefd-4774-b3de-48142fc783fb"

    inputs = [
        InputParam("polyline", CURVE, Access.ITEM),
    ]
    outputs = [
        OutputParam("center_v", AtomicPoint),
        OutputParam("center_e", AtomicPoint),
        OutputParam("center_a", AtomicPoint),
    ]

    def generate(self, polyline=None):
        vertex_centre, edge_centre, area_centre = polygon_centres(polyline)
        return vertex_centre, edge_centre, Component.NO_OUTPUT if area_centre is None else area_centre
