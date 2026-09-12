"""Shear - Shear an object based on a shearing vector (Grasshopper "Shear")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPlane, AtomicPoint, AtomicTransform
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Transforms import apply_transform
from pyhopper.Core.TypeSystem import GEOMETRY


class Shear(Component):
    """Shear an object based on a shearing vector.

    Inputs:
        geometry: Base geometry (Grasshopper Geometry [item]).
        base: Base plane (Grasshopper Base [item]).
        grip: Reference point (Grasshopper Grip [item]).
        target: Target point (Grasshopper Target [item]).

    Outputs:
        geometry: Sheared geometry (Grasshopper Geometry).
        transform: Transformatio data (Grasshopper Transform).

    Notes:
        Grasshopper: Transform > Affine > Shear (Shear).
        pyhopper decisions: the shear that keeps the base plane fixed and moves ``grip`` to ``target``
        (``AtomicTransform.shear``, verified against RhinoCommon); without geometry only the transform
        is emitted; Grasshopper defaults grip = target = (0, 0, 1) (the identity).
    """

    display_name = "Shear"
    nickname = "Shear"
    gh_guid = "5a27203a-e05f-4eea-b80f-a5f29a00fdf2"

    inputs = [
        InputParam("geometry", GEOMETRY, Access.ITEM, optional=True),
        InputParam("base", AtomicPlane, Access.ITEM, default=AtomicPlane.world_xy()),
        InputParam("grip", AtomicPoint, Access.ITEM, default=AtomicPoint(0.0, 0.0, 1.0)),
        InputParam("target", AtomicPoint, Access.ITEM, default=AtomicPoint(0.0, 0.0, 1.0)),
    ]
    outputs = [
        OutputParam("geometry", GEOMETRY),
        OutputParam("transform", AtomicTransform),
    ]

    def generate(self, geometry=None, base=AtomicPlane.world_xy(), grip=AtomicPoint(0.0, 0.0, 1.0), target=AtomicPoint(0.0, 0.0, 1.0)):
        xform = AtomicTransform.shear(base, grip, target)
        return (Component.NO_OUTPUT if geometry is None else apply_transform(xform, geometry)), xform
