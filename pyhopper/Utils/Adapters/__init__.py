"""Utility adapters for geometry interoperability."""

from .shapely_regions import (
    region_boundaries_from_boundary_edges,
    region_difference,
    region_intersection,
    region_union,
    regions_from_boundary_edges,
)

__all__ = [
    "region_boundaries_from_boundary_edges",
    "region_difference",
    "region_intersection",
    "region_union",
    "regions_from_boundary_edges",
]
