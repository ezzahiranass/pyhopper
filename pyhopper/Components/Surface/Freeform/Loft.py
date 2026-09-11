"""Loft - Create a surface through compatible section curves."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicPoint, AtomicSurface
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Nurbs import CurveProfile as _CurveProfile
from pyhopper.Utils.Nurbs import basis_matrix as _basis_matrix
from pyhopper.Utils.Nurbs import collapse_knots, curve_profile
from pyhopper.Utils.Nurbs import interpolation_knots as _interpolation_knots
from pyhopper.Utils.Nurbs import solve_linear_system
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


_TOLERANCE = 1e-12


def _validate_compatible_profiles(profiles: tuple[_CurveProfile, ...]) -> None:
    reference = profiles[0]
    for index, profile in enumerate(profiles[1:], start=2):
        if profile.degree != reference.degree:
            raise ValueError(
                f"Loft requires matching curve degrees; profile 1 has degree "
                f"{reference.degree}, profile {index} has degree {profile.degree}"
            )
        if len(profile.poles) != len(reference.poles):
            raise ValueError(
                "Loft requires matching control point counts; profile 1 has "
                f"{len(reference.poles)}, profile {index} has {len(profile.poles)}"
            )
        if profile.knots != reference.knots or profile.mults != reference.mults:
            raise ValueError(f"Loft requires matching knot structures; profile {index} is incompatible")


def _interpolate_control_grid(
    profiles: tuple[_CurveProfile, ...],
    basis_matrix: list[list[float]],
) -> tuple[tuple[tuple[AtomicPoint, ...], ...], tuple[tuple[float, ...], ...]]:
    row_count = len(profiles)
    column_count = len(profiles[0].poles)
    homogeneous_rows = [[[0.0] * 4 for _ in range(column_count)] for _ in range(row_count)]
    for column in range(column_count):
        section_values = []
        for profile in profiles:
            point = profile.poles[column]
            weight = profile.weights[column]
            section_values.append([point.x * weight, point.y * weight, point.z * weight, weight])
        for row, control in enumerate(solve_linear_system(basis_matrix, section_values, "Loft could not interpolate the section curves")):
            homogeneous_rows[row][column] = control

    poles = []
    weights = []
    for row in homogeneous_rows:
        pole_row = []
        weight_row = []
        for xw, yw, zw, weight in row:
            if abs(weight) <= _TOLERANCE:
                raise ValueError("Loft produced an invalid zero-weight control point")
            pole_row.append(AtomicPoint(xw / weight, yw / weight, zw / weight))
            weight_row.append(weight)
        poles.append(tuple(pole_row))
        weights.append(tuple(weight_row))
    return tuple(poles), tuple(weights)


class Loft(Component):
    """Create one interpolated surface through a branch of section curves.

    Profiles are unified to NURBS and must already share degree, knot
    structure, and control-point count. Automatic profile harmonization and
    custom loft options require a future geometry-kernel adapter.
    """

    inputs = [InputParam("curves", None, Access.LIST)]
    outputs = [OutputParam("surface", AtomicSurface)]

    def generate(self, curves=None):
        if curves is None or len(curves) < 2:
            raise ValueError("Loft requires at least two section curves")

        profiles = tuple(curve_profile(as_nurbs_curve(curve), "Loft", _TOLERANCE) for curve in curves)
        _validate_compatible_profiles(profiles)
        section_count = len(profiles)
        v_degree = min(3, section_count - 1)
        parameters = tuple(index / (section_count - 1) for index in range(section_count))
        full_v_knots = _interpolation_knots(parameters, v_degree)
        v_knots, v_mults = collapse_knots(full_v_knots, _TOLERANCE)
        poles, weights = _interpolate_control_grid(
            profiles,
            _basis_matrix(parameters, full_v_knots, v_degree),
        )
        reference = profiles[0]
        return AtomicSurface(
            poles=poles,
            weights=weights,
            u_knots=reference.knots,
            v_knots=v_knots,
            u_mults=reference.mults,
            v_mults=v_mults,
            u_degree=reference.degree,
            v_degree=v_degree,
        )
