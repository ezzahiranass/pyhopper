"""WeightedAverage - Solve the arithmetic weighted average for a set of items (Grasshopper "Weighted Average")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicPoint, AtomicVector

from .._arith import Spatial, is_number


class WeightedAverage(Component):
    """Solve the arithmetic weighted average for a set of items.

    Inputs:
        input: Input values for averaging (Grasshopper Input [list]).
        weights: Collection of weights for each value (Grasshopper Weights [list]).

    Outputs:
        arithmetic_mean: Arithmetic mean (average) of all input values (Grasshopper Arithmetic mean).

    Notes:
        Grasshopper: Maths > Util > Weighted Average (Wav).
        pyhopper decisions: ``sum(w * x) / sum(w)`` for numbers, vectors or points (weights may be
        negative); Grasshopper-verified errors become ``ValueError``: the weight count must equal the
        value count and the weights must not sum to zero. An empty list emits nothing.
    """

    display_name = "Weighted Average"
    nickname = "Wav"
    gh_guid = "338666eb-14c5-4d9b-82e2-2b5be60655df"

    inputs = [
        InputParam("input", None, Access.LIST),
        InputParam("weights", float, Access.LIST),
    ]
    outputs = [
        OutputParam("arithmetic_mean"),
    ]

    def generate(self, input=None, weights=None):
        items = list(input or [])
        factors = [float(weight) for weight in (weights or [])]
        if not items:
            return Component.NO_OUTPUT
        if len(factors) != len(items):
            raise ValueError("WeightedAverage needs one weight per value")
        total = sum(factors)
        if total == 0.0:
            raise ValueError("WeightedAverage weights must not sum to zero")
        if all(is_number(item) for item in items):
            return sum(float(item) * weight for item, weight in zip(items, factors)) / total
        if all(isinstance(item, Spatial) for item in items):
            x = sum(item.x * weight for item, weight in zip(items, factors)) / total
            y = sum(item.y * weight for item, weight in zip(items, factors)) / total
            z = sum(item.z * weight for item, weight in zip(items, factors)) / total
            result_type = AtomicPoint if any(isinstance(item, AtomicPoint) for item in items) else AtomicVector
            return result_type(x, y, z)
        raise TypeError("WeightedAverage needs a list of numbers, vectors or points")
