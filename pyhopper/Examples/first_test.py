"""
First pyhopper example — a parametric tower exported to GLB.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pyhopper import (
    CircleCmp, DivideCurve, Series, UnitZ,
    Move, Rotate, Polygon, CylinderCmp, LineCmp,
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
grid_points    = DivideCurve(base_circle, count=NUM_COLUMNS)
z_vec          = UnitZ()

levels         = Series(start=0, step=FLOOR_HEIGHT, count=NUM_FLOORS)
floor_points   = Move(grid_points, z_vec, levels.graft())

angles         = Series(start=0, step=TWIST_DEG, count=NUM_FLOORS)
rotated_floors = Rotate(floor_points, axis=z_vec, angle=angles.graft())
floor_polygons = Polygon(rotated_floors)

top_points = Move(grid_points, z_vec, FLOOR_HEIGHT * NUM_FLOORS)
columns    = LineCmp(grid_points, top_points)
core       = CylinderCmp(radius=CORE_RADIUS, height=FLOOR_HEIGHT * NUM_FLOORS)

tower  = Merge(floor_polygons, columns, core)
output = os.path.join(os.path.dirname(__file__), "tower.glb")
export_glb(tower, output)
print(f"Exported {len(tower)} objects -> {output}")
