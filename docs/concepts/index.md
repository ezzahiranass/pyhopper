# Concepts

pyhopper is built on three interlocking ideas taken directly from Grasshopper's data model.
Understanding them makes everything else predictable.

| Concept | One line |
|---------|----------|
| [Atoms](atoms.md) | Immutable geometric primitives — the leaves of every DataTree |
| [DataTree](data-tree.md) | The hierarchical container that carries data between components |
| [Components](components.md) | Processing nodes — the only things allowed to transform data |

Read them in order if you're new; jump to whichever is relevant if you're debugging a tree mismatch.
