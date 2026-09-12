"""Loft - Create a surface through compatible section curves."""

from __future__ import annotations

from dataclasses import dataclass

from pyhopper.Core.Atoms import AtomicNurbsCurve, AtomicPoint, AtomicSurface, _open_uniform_bspline_data
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Unifiers.unitypes import as_nurbs_curve


_TOLERANCE = 1e-12


@dataclass(frozen=True)
class _CurveProfile:
    poles: tuple[AtomicPoint, ...]
    weights: tuple[float, ...]
    knots: tuple[float, ...]
    mults: tuple[int, ...]
    degree: int


def _collapse_repeated_knots(knots: tuple[float, ...]) -> tuple[tuple[float, ...], tuple[int, ...]]:
    unique_knots = [knots[0]]
    multiplicities = [1]
    for knot in knots[1:]:
        if abs(knot - unique_knots[-1]) <= _TOLERANCE:
            multiplicities[-1] += 1
        else:
            unique_knots.append(knot)
            multiplicities.append(1)
    return tuple(unique_knots), tuple(multiplicities)


def _nurbs_profile(curve: AtomicNurbsCurve) -> _CurveProfile:
    if len(curve.control_points) < 2:
        raise ValueError("Loft requires curves with at least two control points")

    degree = max(1, min(int(curve.degree), len(curve.control_points) - 1))
    weights = curve.weights if len(curve.weights) == len(curve.control_points) else tuple(
        1.0 for _ in curve.control_points
    )
    if not curve.knots:
        knots, mults, degree = _open_uniform_bspline_data(len(curve.control_points), degree)
    else:
        raw_knots = tuple(float(knot) for knot in curve.knots)
        expected_full_count = len(curve.control_points) + degree + 1
        expected_unique_count = len(curve.control_points) - degree + 1
        if len(raw_knots) == expected_full_count:
            knots, mults = _collapse_repeated_knots(raw_knots)
        elif len(raw_knots) == expected_unique_count:
            knots = raw_knots
            mults = tuple(
                degree + 1 if index in (0, len(knots) - 1) else 1
                for index in range(len(knots))
            )
        else:
            raise ValueError(
                "Loft could not interpret a profile knot vector; expected either "
                "a full knot vector or a unique-knot sequence matching its control point count."
            )
    return _CurveProfile(curve.control_points, weights, knots, mults, degree)


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


def _interpolation_knots(parameters: tuple[float, ...], degree: int) -> tuple[float, ...]:
    interior = tuple(
        sum(parameters[index:index + degree]) / degree
        for index in range(1, len(parameters) - degree)
    )
    return (parameters[0],) * (degree + 1) + interior + (parameters[-1],) * (degree + 1)


def _find_span(degree: int, knots: tuple[float, ...], point_count: int, parameter: float) -> int:
    if parameter >= knots[point_count]:
        return point_count - 1
    low = degree
    high = point_count
    mid = (low + high) // 2
    while parameter < knots[mid] or parameter >= knots[mid + 1]:
        if parameter < knots[mid]:
            high = mid
        else:
            low = mid
        mid = (low + high) // 2
    return mid


def _basis_functions(span: int, parameter: float, degree: int, knots: tuple[float, ...]) -> list[float]:
    basis = [0.0] * (degree + 1)
    basis[0] = 1.0
    left = [0.0] * (degree + 1)
    right = [0.0] * (degree + 1)
    for order in range(1, degree + 1):
        left[order] = parameter - knots[span + 1 - order]
        right[order] = knots[span + order] - parameter
        saved = 0.0
        for index in range(order):
            denominator = right[index + 1] + left[order - index]
            term = 0.0 if abs(denominator) <= _TOLERANCE else basis[index] / denominator
            basis[index] = saved + right[index + 1] * term
            saved = left[order - index] * term
        basis[order] = saved
    return basis


def _basis_matrix(parameters: tuple[float, ...], knots: tuple[float, ...], degree: int) -> list[list[float]]:
    point_count = len(parameters)
    matrix = [[0.0] * point_count for _ in parameters]
    for row, parameter in enumerate(parameters):
        span = _find_span(degree, knots, point_count, parameter)
        for local_index, value in enumerate(_basis_functions(span, parameter, degree, knots)):
            matrix[row][span - degree + local_index] = value
    return matrix


def _solve_linear_system(matrix: list[list[float]], values: list[list[float]]) -> list[list[float]]:
    size = len(matrix)
    augmented = [matrix[row][:] + values[row][:] for row in range(size)]
    value_count = len(values[0])
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= _TOLERANCE:
            raise ValueError("Loft could not interpolate the section curves")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if abs(factor) <= _TOLERANCE:
                continue
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column])
            ]
    return [row[size:size + value_count] for row in augmented]


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
        for row, control in enumerate(_solve_linear_system(basis_matrix, section_values)):
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

        profiles = tuple(_nurbs_profile(as_nurbs_curve(curve)) for curve in curves)
        _validate_compatible_profiles(profiles)
        section_count = len(profiles)
        v_degree = min(3, section_count - 1)
        parameters = tuple(index / (section_count - 1) for index in range(section_count))
        full_v_knots = _interpolation_knots(parameters, v_degree)
        v_knots, v_mults = _collapse_repeated_knots(full_v_knots)
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
