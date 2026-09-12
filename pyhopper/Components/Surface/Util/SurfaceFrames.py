"""SurfaceFrames - Generate a grid of {uv} frames on a surface (Grasshopper "Surface Frames")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree
from pyhopper.Utils.Differential import surface_analysis, surface_grid_parameters
from pyhopper.Core.TypeSystem import SURFACE


class SurfaceFrames(Component):
    """Generate a grid of {uv} frames on a surface.

    Inputs:
        surface: Surface to divide (Grasshopper Surface [item]).
        u_count: Number of segments in U-direction (Grasshopper U Count [item]).
        v_count: Number of segments in V-direction (Grasshopper V Count [item]).

    Outputs:
        frames: Surface Frames (Grasshopper Frames).
        parameters: Parameter coordinates at division points (Grasshopper Parameters).

    Notes:
        Grasshopper: Surface > Util > Surface Frames (SFrames).
        pyhopper decisions: Grasshopper-verified — one branch per U step at ``{path;iteration;u}``
        holding the frames along V (origin at the point, x along U, normal along the surface normal)
        and the (u, v) parameters as points; zero counts give empty trees, negative counts raise
        ``ValueError``. Defaults 10 x 10.
    """

    display_name = "Surface Frames"
    nickname = "SFrames"
    gh_guid = "332378f4-acb2-43fe-8593-ed22bfeb2721"

    inputs = [
        InputParam("surface", SURFACE, Access.ITEM),
        InputParam("u_count", int, Access.ITEM, default=10),
        InputParam("v_count", int, Access.ITEM, default=10),
    ]
    outputs = [
        OutputParam("frames", AtomicPlane, access=Access.TREE),
        OutputParam("parameters", AtomicPoint, access=Access.TREE),
    ]

    def generate(self, surface=None, u_count=10, v_count=10):
        u_segments, v_segments = int(u_count), int(v_count)
        if u_segments < 0 or v_segments < 0:
            raise ValueError("SurfaceFrames needs non-negative segment counts")
        if not u_segments or not v_segments:
            return DataTree(), DataTree()
        us, vs = surface_grid_parameters(surface, u_segments, v_segments)
        return (
            self.sub_branches([[surface_analysis(surface, u, v).frame for v in vs] for u in us]),
            self.sub_branches([[AtomicPoint(u, v, 0.0) for v in vs] for u in us]),
        )
