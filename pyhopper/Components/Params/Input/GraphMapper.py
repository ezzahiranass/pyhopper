"""GraphMapper - Remap numeric DataTree items through an authored function."""

from __future__ import annotations

import math
from typing import Any

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.DataTree import DataTree


GRAPH_TYPES = frozenset({"linear", "bezier", "sine", "gaussian"})


def evaluate_graph(
    value: float,
    *,
    graph_type: str = "bezier",
    x_min: float = 0.0,
    x_max: float = 1.0,
    y_min: float = 0.0,
    y_max: float = 1.0,
    control_y1: float = 0.15,
    control_y2: float = 0.85,
) -> float:
    """Evaluate one number against a clamped normalized graph function."""
    if graph_type not in GRAPH_TYPES:
        raise ValueError(f"Unsupported GraphMapper graph type: {graph_type}")

    x_span = x_max - x_min
    t = 0.0 if x_span == 0.0 else (float(value) - x_min) / x_span
    t = min(max(t, 0.0), 1.0)

    if graph_type == "linear":
        mapped = t
    elif graph_type == "sine":
        mapped = 0.5 - 0.5 * math.cos(math.pi * t)
    elif graph_type == "gaussian":
        sigma = 0.18
        mapped = math.exp(-((t - 0.5) ** 2) / (2.0 * sigma**2))
    else:
        inverse = 1.0 - t
        mapped = (
            3.0 * inverse * inverse * t * control_y1
            + 3.0 * inverse * t * t * control_y2
            + t**3
        )

    return y_min + mapped * (y_max - y_min)


def map_graph_tree(tree: Any, config: dict[str, Any] | None = None) -> DataTree:
    """Map every numeric item while preserving DataTree paths and cardinality."""
    settings = config or {}
    source = DataTree.coerce(tree)
    branches = {}
    for path, branch in source.branches():
        mapped_items = []
        for item in branch:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise TypeError(f"GraphMapper expected numeric items, got {type(item).__name__}")
            mapped_items.append(
                evaluate_graph(
                    item,
                    graph_type=str(settings.get("graphType", "bezier")),
                    x_min=float(settings.get("xMin", 0.0)),
                    x_max=float(settings.get("xMax", 1.0)),
                    y_min=float(settings.get("yMin", 0.0)),
                    y_max=float(settings.get("yMax", 1.0)),
                    control_y1=float(settings.get("controlY1", 0.15)),
                    control_y2=float(settings.get("controlY2", 0.85)),
                )
            )
        branches[path] = mapped_items
    return DataTree.from_branches(branches)


class GraphMapper(Component):
    """Map numeric items through a graph while preserving the input DataTree."""

    inputs = [InputParam("numbers", float, Access.ITEM)]
    outputs = [OutputParam("mapped", float)]
    settings_schema = {
        "graphType": {"type": "choice", "default": "bezier", "choices": sorted(GRAPH_TYPES)},
        "xMin": {"type": "float", "default": 0.0},
        "xMax": {"type": "float", "default": 1.0},
        "yMin": {"type": "float", "default": 0.0},
        "yMax": {"type": "float", "default": 1.0},
        "controlY1": {"type": "float", "default": 0.15},
        "controlY2": {"type": "float", "default": 0.85},
    }

    def generate(self, numbers=0.0) -> float:
        return evaluate_graph(float(numbers))
