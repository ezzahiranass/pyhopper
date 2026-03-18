"""DivideCurve - Divide a curve into evenly spaced points."""

import math

from pyhopper.Core.Atoms import AtomicCircle, AtomicLine, AtomicPoint
from pyhopper.Core.Component import Component, InputParam, OutputParam, Access


class DivideCurve(Component):
    """Divide a curve into evenly spaced ``AtomicPoint`` samples.

    Accepts an ``AtomicCircle``, ``AtomicArc``, ``AtomicPolyline``, or
    ``AtomicNurbsCurve`` and returns
    ``count`` points in a single output branch per input curve.
    """

    inputs = [
        InputParam("curve", None, Access.ITEM),
        InputParam("count", int, Access.ITEM, default=10),
    ]
    outputs = [OutputParam("points")]

    def generate(self, curve=None, count=10):
        segment_count = int(count)

        if isinstance(curve, AtomicCircle):
            center = curve.plane.origin
            radius = curve.radius
            x_axis = curve.plane.x_axis
            y_axis = curve.plane.y_axis

            return [
                AtomicPoint(
                    center.x + radius * (math.cos((2.0 * math.pi * index) / segment_count) * x_axis.x + math.sin((2.0 * math.pi * index) / segment_count) * y_axis.x),
                    center.y + radius * (math.cos((2.0 * math.pi * index) / segment_count) * x_axis.y + math.sin((2.0 * math.pi * index) / segment_count) * y_axis.y),
                    center.z + radius * (math.cos((2.0 * math.pi * index) / segment_count) * x_axis.z + math.sin((2.0 * math.pi * index) / segment_count) * y_axis.z),
                )
                for index in range(segment_count)
            ]

        if isinstance(curve, AtomicLine):
            return [
                AtomicPoint(
                    curve.start.x + (index / segment_count) * (curve.end.x - curve.start.x),
                    curve.start.y + (index / segment_count) * (curve.end.y - curve.start.y),
                    curve.start.z + (index / segment_count) * (curve.end.z - curve.start.z),
                )
                for index in range(segment_count + 1)
            ]

        raise TypeError(f"Cannot divide curve of type {type(curve).__name__}")
