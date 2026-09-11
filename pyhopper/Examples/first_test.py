"""
First pyhopper example — a parametric tower exported to GLB.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pyhopper import (
    CircleCmp, DivideCurve, Series, UnitZ, XYPlane,
    Move, Rotate, Polyline, CylinderCmp, LineCmp,
    Merge,
)
from pyhopper.Utils.Exporters import export_glb

NUM_FLOORS   = 20
NUM_COLUMNS  = 12
FLOOR_HEIGHT = 3.5
BASE_RADIUS  = 20.0
TWIST_DEG    = 3.0
CORE_RADIUS  = 6.0

base_circle    = CircleCmp(radius=BASE_RADIUS)
grid_points    = DivideCurve(base_circle, count=NUM_COLUMNS)          # {0}: 12 points (closed curve → 12)

levels         = Series(start=0, step=FLOOR_HEIGHT, count=NUM_FLOORS)  # {0}: 20 heights
lift_vectors   = UnitZ(levels.graft())                                  # {0;i}: one (0, 0, height) vector per floor
floor_points   = Move(grid_points, lift_vectors)                        # {0;i}: 12 points per floor

angles         = Series(start=0, step=math.radians(TWIST_DEG), count=NUM_FLOORS)
rotated_floors = Rotate(floor_points, angles.graft(), XYPlane())        # twist each floor about world Z
floor_polygons = Polyline(rotated_floors, closed=True)                  # {0;i}: one closed outline per floor

top_points = Move(grid_points, UnitZ(FLOOR_HEIGHT * NUM_FLOORS))
columns    = LineCmp(grid_points, top_points)                           # {0}: 12 columns
core       = CylinderCmp(radius=CORE_RADIUS, length=FLOOR_HEIGHT * NUM_FLOORS)

tower  = Merge(floor_polygons, columns, core)
output = os.path.join(os.path.dirname(__file__), "tower.glb")
export_glb(tower, output)
print(f"Exported {len(tower)} objects -> {output}")
