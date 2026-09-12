# Declarative Definition Contract

This project should allow a pyhopper definition to read like a Grasshopper graph.

## Rules

- Define each step as one component call.
- Pass plain values, atoms, branches, `DataTree`s, or prior component results directly.
- Prefer `next_comp = NextComponent(prev_comp, value, other_comp)`.
- Assign literal atoms to variables before feeding them into components.
- Assign a number to a variable when it is a knob worth exposing: the studio importer turns
  named numbers into sliders. Pass a constant inline (`Polygon(plane, 1.5, 6, 0.0)`) when it is a
  fixed setting: it stays on that input port as an inline literal (numbers, booleans and text on
  `float`/`int`/`bool`/`str` inputs; a wire on the same input always wins).
- Do not reach into atom internals such as `.normal`, `.x_axis`, `.points`, `.line`.
- Do not index into outputs or lists inside the definition (`[0]`, `[12]`, `["key"]`).
- Do not reshape component outputs manually in the definition layer.
- If the graph needs a datum like a plane, axis, or vector, add a proper component for it.
- Keep component definitions inline on one line when feasible.
- a component can return one or multiple outputs, check the component class before using it

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

## Tree Operations

a tree operation can either be at the level of an input or an output
tree operations do not mutate the state of the variable, which is what we want.
input ops are declared inline inside the component object call, output ops are done the line after, look at the example

```python
circle = Circle(2.0, plane)
polygon = Polygon(plane.graft(), 1.5, 6, 0.0) #tree op on one of the inputs
scene = Merge(circle, polygon)
scene.simplify() #tree op on one of the outputs
```
## Intent

The definition layer should describe the graph, not inspect the data model.
If a definition feels forced to extract fields from atoms, the missing piece is
usually a component that should exist in the library.
