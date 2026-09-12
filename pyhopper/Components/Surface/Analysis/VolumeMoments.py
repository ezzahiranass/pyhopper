"""VolumeMoments - Solve volume properties for closed breps and meshes (Grasshopper "Volume Moments")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicVector
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.MassProperties import volume_moments
from pyhopper.Core.TypeSystem import GEOMETRY


class VolumeMoments(Component):
    """Solve volume properties for closed breps and meshes.

    Inputs:
        geometry: Closed brep or mesh for volume computation (Grasshopper Geometry [item]).

    Outputs:
        volume: Volume of geometry (Grasshopper Volume).
        centroid: Volume centroid of geometry (Grasshopper Centroid).
        inertia: Moments of inertia around the centroid (Grasshopper Inertia).
        secondary: Secondary moments of inertia around the centroid (Grasshopper Secondary).
        gyration: Radii of gyration (Grasshopper Gyration).

    Notes:
        Grasshopper: Surface > Analysis > Volume Moments (VMoments).
        pyhopper decisions: Grasshopper-verified for boxes — volume, centroid and, about the centroid
        in world axes, the moments of inertia, second moments and radii of gyration, integrated over
        tetrahedra from the vertex average (exact for convex closed shells); open geometry raises
        ``ValueError`` where Grasshopper emits zeros with a warning.
    """

    display_name = "Volume Moments"
    nickname = "VMoments"
    gh_guid = "2e685fd9-7b8f-461b-b330-44857b099937"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM),
    ]
    outputs = [
        OutputParam("volume", float),
        OutputParam("centroid", AtomicPoint),
        OutputParam("inertia", AtomicVector),
        OutputParam("secondary", AtomicVector),
        OutputParam("gyration", AtomicVector),
    ]

    def generate(self, geometry=None):
        return volume_moments(geometry)
