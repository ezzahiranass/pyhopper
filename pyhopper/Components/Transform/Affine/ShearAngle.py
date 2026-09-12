"""ShearAngle - Shear an object based on tilt angles (Grasshopper "Shear Angle")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform

from .._geometry import shear_by_angles
from pyhopper.Core.TypeSystem import GEOMETRY


class ShearAngle(Component):
    """Shear an object based on tilt angles.

    Inputs:
        geometry: Base geometry (Grasshopper Geometry [item]).
        base: Base plane (Grasshopper Base [item]).
        angle_x: Rotation around {x} axis in radians (Grasshopper Angle X [item]).
        angle_y: Rotation around {y} axis in radians (Grasshopper Angle Y [item]).

    Outputs:
        geometry: Sheared geometry (Grasshopper Geometry).
        transform: Transformation data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Affine > Shear Angle (Shear).
        pyhopper decisions: Grasshopper-verified — the base plane's z axis tilts by ``angle_x`` about
        the x axis and then by ``angle_y`` about the y axis while x and y stay put; tilts of 90 degrees
        or more (a flattened frame) raise ``ValueError``. Without geometry only the transform is emitted.
    """

    display_name = "Shear Angle"
    nickname = "Shear"
    gh_guid = "f19ee36c-f21f-4e25-be4c-4ca4b30eda0d"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM, optional=True),
        InputParam("base", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("angle_x", float, Access.ITEM, default=0.0),
        InputParam("angle_y", float, Access.ITEM, default=0.0),
    ]
    outputs = [
        OutputParam("geometry", GEOMETRY),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, base=AtomicPlane.world_xy(), angle_x=0.0, angle_y=0.0):
        xform = shear_by_angles(base, float(angle_x), float(angle_y))
        return (Component.NO_OUTPUT if geometry is None else apply_transform(xform, geometry)), xform
