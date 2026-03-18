# Declarative Definition Contract

This project should allow a pyhopper definition to read like a Grasshopper graph.

## Rules

- Define each step as one component call.
- Pass plain values, atoms, branches, `DataTree`s, or prior component results directly.
- Prefer `next_comp = NextComponent(prev_comp, value, other_comp)`.
- Prefer assigning literal atoms and literal numbers to variables before feeding them into components.
- Do not reach into atom internals such as `.normal`, `.x_axis`, `.points`, `.line`.
- Do not index into outputs or lists inside the definition (`[0]`, `[12]`, `["key"]`).
- Do not reshape component outputs manually in the definition layer.
- If the graph needs a datum like a plane, axis, or vector, add a proper component for it.
- Keep component definitions inline on one line when feasible.

## Shape

```python
origin = AtomicPoint(5.0, 0.0, 0.0)
x_axis = UnitX()
y_axis = UnitY()
plane = ConstructPlane(origin, x_axis, y_axis)
circle = Circle(2.0, plane)
polygon = Polygon(plane, 1.5, 6, 0.0)
scene = Merge(circle, polygon)
```

## Intent

The definition layer should describe the graph, not inspect the data model.
If a definition feels forced to extract fields from atoms, the missing piece is
usually a component that should exist in the library.
