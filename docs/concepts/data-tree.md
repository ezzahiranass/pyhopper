# Data Tree

A `DataTree` is an ordered dictionary of **Branches**, each addressed by a **Path**.

```
DataTree
 ├── {0;0} → [Point3d(0,0,0), Point3d(5,0,0), Point3d(10,0,0)]
 ├── {0;1} → [Point3d(0,0,3), Point3d(5,0,3), Point3d(10,0,3)]
 └── {0;2} → [Point3d(0,0,6), Point3d(5,0,6), Point3d(10,0,6)]
```

---

## Path

A `Path` is an immutable tuple of non-negative integers printed in Grasshopper notation:

```python
from pyhopper import Path

p = Path(0, 2, 1)   # address {0;2;1}
p.depth             # 3
str(p)              # '{0;2;1}'
```

Paths are compared and sorted lexicographically, so `{0;1}` comes before `{0;2}`.

---

## Branch

A `Branch` is a plain Python list that knows its own path:

```python
from pyhopper import Branch, Path

b = Branch(Path(0, 1), [10, 20, 30])
b.path   # Path(0, 1)
b[0]     # 10
```

---

## Creating trees

```python
from pyhopper import DataTree, Path

# Single item at {0}
tree = DataTree.from_item(42)

# Flat list at {0}
tree = DataTree.from_list([1, 2, 3])

# Explicit branch mapping
tree = DataTree.from_branches({
    Path(0): [1, 2, 3],
    Path(1): [4, 5, 6],
})

# Coerce any value (DataTree passes through, scalars wrap to {0})
tree = DataTree.coerce(some_value)
```

---

## Tree operations

All operations return a **new** DataTree — trees are never mutated.

### `graft()`

Each item becomes its own single-item branch. Item at `{a;b}[i]` moves to `{a;b;i}[0]`.

```python
tree = DataTree.from_list([10, 20, 30])
# {0}: [10, 20, 30]

grafted = tree.graft()
# {0;0}: [10]
# {0;1}: [20]
# {0;2}: [30]
```

**When to use it:** You have a list of *parameters* (heights, angles, counts) and want
each one to pair with a separate copy of the geometry in the next component.

### `flatten()`

Collapse all branches into a single branch at `{0}`.

```python
tree.flatten()
# {0}: [10, 20, 30, 40, ...]
```

### `simplify()`

Remove the longest common path prefix from all branches.

```python
# {0;0}: [a]
# {0;1}: [b]
# simplify → {0}: [a]  {1}: [b]
```

### `flip_matrix()`

Transpose branches and items: N branches of M items → M branches of N items.

---

## Data matching

When a component has multiple inputs, their trees are **matched** before `generate()` is
called. The default rule is **Longest List** (same as Grasshopper's default):

- Branch matching: the tree with the most branches drives iteration; shorter trees
  repeat their last branch.
- Item matching within a branch: shorter lists repeat their last item.

```python
# geometry:  {0}: [A, B, C]          (1 branch, 3 items)
# distance:  {0;0}: [1]              (grafted, 1 item each)
#            {0;1}: [2]
#            {0;2}: [3]
#
# Result: 3 calls per level → 9 output items across 3 branches
```

Other rules (`SHORTEST_LIST`, `CROSS_REFERENCE`) can be set on the component:

```python
class MyComp(Component):
    match_rule = MatchRule.CROSS_REFERENCE
```

---

## Serialization

Every DataTree and every Atom implements `to_json()` / `from_json()`:

```python
json_str = tree.to_json_string(indent=2)
restored = DataTree.from_json(json.loads(json_str))
```

Items are dispatched by their `"type"` field through `ATOM_REGISTRY`, so any custom
Atom you register is automatically round-trippable.

---

## API reference

See the full [DataTree reference](../reference/Core/DataTree.md),
[Branch reference](../reference/Core/Branch.md), and
[Path reference](../reference/Core/Path.md).
