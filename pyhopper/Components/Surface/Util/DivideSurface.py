"""DivideSurface - Generate a grid of {uv} points on a surface (Grasshopper "Divide Surface")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Utils.Differential import surface_analysis, surface_grid_parameters
from pyhopper.Core.TypeSystem import SURFACE


class DivideSurface(Component):
    """Generate a grid of {uv} points on a surface.

    Inputs:
        surface: Surface to divide (Grasshopper Surface [item]).
        u_count: Number of segments in {u} direction (Grasshopper U Count [item]).
        v_count: Number of segments in {v} direction (Grasshopper V Count [item]).

    Outputs:
        points: Division points (Grasshopper Points).
        normals: Normal vectors at division points (Grasshopper Normals).
        parameters: Parameter coordinates at division points (Grasshopper Parameters).

    Notes:
        Grasshopper: Surface > Util > Divide Surface (SDivide).
        pyhopper decisions: Grasshopper-verified — one branch per U step at ``{path;iteration;u}``
        holding the V samples: points, unit normals and the (u, v) parameters as points; a zero count
        gives empty trees and negative counts raise ``ValueError``. Defaults 10 x 10.
    """

    display_name = "Divide Surface"
    nickname = "SDivide"
    gh_guid = "5106bafc-d5d4-4983-83e7-7be3ed07f502"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("u_count", int, Access.ITEM, default=10),
        InputParam("v_count", int, Access.ITEM, default=10),
    ]
    outputs = [
        OutputParam("points", AtomicPoint, access=Access.TREE),
        OutputParam("normals", AtomicVector, access=Access.TREE),
        OutputParam("parameters", AtomicPoint, access=Access.TREE),
    ]

    def generate(self, surface=None, u_count=10, v_count=10):
        u_segments, v_segments = int(u_count), int(v_count)
        if u_segments < 0 or v_segments < 0:
            raise ValueError("DivideSurface needs non-negative segment counts")
        if not u_segments or not v_segments:
            return DataTree(), DataTree(), DataTree()
        us, vs = surface_grid_parameters(surface, u_segments, v_segments)
        rows = [[surface_analysis(surface, u, v) for v in vs] for u in us]
        return (
            self.sub_branches([[a.point for a in row] for row in rows]),
            self.sub_branches([[a.normal for a in row] for row in rows]),
            self.sub_branches([[AtomicPoint(u, v, 0.0) for v in vs] for u in us]),
        )
