# Components

A **Component** is a processing node that reads DataTrees, calls `generate()` once per
matched item (or branch, or tree), and returns a new DataTree.

Calling a component looks like a function call. The result is always a `ComponentResult`
that also exposes named secondary outputs as attributes.

---

## Anatomy of a component

```python
from pyhopper.Core.Component import Component, InputParam, OutputParam, Access

class Move(Component):
    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("direction", Vector3d, Access.ITEM, default=None),
        InputParam("distance", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("geometry")]

    def generate(self, geometry=None, direction=None, distance=1.0):
        return ...
```

- `inputs` declares the parameter names, types, access mode, and defaults.
- `generate()` receives **one matched item per input** on each call.
- Whatever `generate()` returns is appended to the output branch for the current path.

---

## Access modes

| Mode | `generate()` receives | Use when |
|------|-----------------------|----------|
| `Access.ITEM` | One item per input | per-item math / geometry ops |
| `Access.LIST` | One `list` per input (full branch) | need to look at all items together |
| `Access.TREE` | Full `DataTree` per input | need full tree awareness |

The access mode is determined by the **highest** mode declared on any input.

---

## The solve pipeline

When you call `Move(geometry, direction, distance)`:

1. **Coerce inputs**: every argument is wrapped in a DataTree via `DataTree.coerce()`.
2. **Match**: `DataTree.match()` aligns branches and items across all input trees.
3. **Iterate**: for each matched `(path, items)` tuple, call `generate(**kw)`.
4. **Collect**: return values are appended to output branches, preserving path structure.
5. **Return**: a `ComponentResult` is returned. Multi-output components expose secondary outputs as attributes.

---

## Graft and the matching engine

The most important pattern in pyhopper is using `.graft()` to force a
one-to-one relationship between parameters and geometry:

```python
levels = Series(start=0, step=3.5, count=20)
# {0}: [0, 3.5, 7, ..., 66.5]

floors = Move(points, z, levels.graft())
# levels.graft() -> {0;0}: [0]   {0;1}: [3.5]  ...  {0;19}: [66.5]
#
# Match:  points {0}:12 items   x   levels {0;0}...{0;19}: 1 item each
# Result: 20 branches x 12 points = 240 output items
```

Without `.graft()`, all 20 heights would be in one branch and zip
against the 12 points via longest-list, giving only 20 outputs total,
all at the same path `{0}`.

---

## Multi-output components

If `generate()` returns a tuple, each element maps to the corresponding output:

```python
class DeconstructPoint(Component):
    inputs = [InputParam("point", Point3d, Access.ITEM)]
    outputs = [OutputParam("x"), OutputParam("y"), OutputParam("z")]

    def generate(self, point=None):
        return point.x, point.y, point.z

result = DeconstructPoint(some_points)
x_values = result.x
y_values = result.y
z_values = result.z
```

---

## Defining a new component

1. Subclass `Component`.
2. Declare `inputs` and `outputs`.
3. Implement `generate()`; it must be stateless and side-effect-free.
4. Register it in `__init__.py` if you want it importable from the top level.

```python
class Scale(Component):
    inputs = [
        InputParam("geometry", None, Access.ITEM),
        InputParam("factor", float, Access.ITEM, default=1.0),
    ]
    outputs = [OutputParam("geometry")]

    def generate(self, geometry=None, factor=1.0):
        return ...
```

That is all. The entire DataTree plumbing is inherited from `Component`.
The component's math or geometry logic should live directly inside `generate()`.

---

## API reference

See the full [Component reference](../reference/Core/Component.md), including
`Component`, `InputParam`, `OutputParam`, `Access`, and `ComponentResult`.
