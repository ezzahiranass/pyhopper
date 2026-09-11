"""Component discovery by walking ``pyhopper/Components/**``.

The module path is the component's identity: the first folder is the
Grasshopper tab, the folders below it the category, the class name the
component. Nothing needs registering — dropping a module into the tree makes
it visible to the web catalog, the docs generator and ``import pyhopper``
(``pyhopper.SomeComponent`` resolves lazily through :func:`resolve`).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from inspect import getmembers, isclass
from pathlib import Path
from types import ModuleType
from typing import Iterator

from pyhopper.Core.Component import Component

COMPONENTS_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ComponentEntry:
    tab: str
    category: str
    key: str
    cls: type[Component]

    @property
    def name(self) -> str:
        return self.cls.__name__


def iter_component_modules() -> Iterator[tuple[str, str, ModuleType]]:
    """Yield ``(tab, category, module)`` for every component module under the tree.

    Files starting with ``_`` (helpers) and this module are skipped; a module
    directly inside a tab folder gets the category ``General``.
    """
    for src_path in sorted(COMPONENTS_ROOT.rglob("*.py")):
        if src_path.name.startswith("_") or src_path.resolve() == Path(__file__).resolve():
            continue
        rel_parts = src_path.relative_to(COMPONENTS_ROOT).with_suffix("").parts
        if len(rel_parts) < 2:
            continue  # nothing lives directly in Components/
        tab = rel_parts[0]
        category = "/".join(rel_parts[1:-1]) if len(rel_parts) > 2 else "General"
        module = import_module(".".join(("pyhopper", "Components", *rel_parts)))
        yield tab, category, module


def iter_component_classes() -> Iterator[ComponentEntry]:
    """Yield every concrete component class defined (not merely imported) in the tree."""
    for tab, category, module in iter_component_modules():
        for _, member in getmembers(module, isclass):
            if member is Component or not issubclass(member, Component):
                continue
            if member.__module__ != module.__name__:
                continue  # re-exports (e.g. Curve/Primitive/Cylinder) are not new components
            yield ComponentEntry(tab, category, component_key(member), member)


def component_key(component_cls: type[Component]) -> str:
    """Fully qualified identity used by the compiler and the web catalog."""
    return f"{component_cls.__module__}.{component_cls.__name__}"


@lru_cache(maxsize=1)
def component_index() -> dict[str, tuple[ComponentEntry, ...]]:
    """Class name -> entries (several when the same name exists in different tabs)."""
    index: dict[str, list[ComponentEntry]] = {}
    for entry in iter_component_classes():
        index.setdefault(entry.name, []).append(entry)
    return {name: tuple(entries) for name, entries in index.items()}


def resolve(name: str) -> type[Component]:
    """Resolve a bare class name to a component class.

    Parameter containers (the ``Params`` tab) yield to same-named components in
    other tabs, so ``resolve("Circle")`` is the Curve primitive. An ambiguous
    name outside ``Params`` raises ``LookupError`` listing the candidates.
    """
    entries = component_index().get(name)
    if not entries:
        raise LookupError(f"No component named {name!r}")
    non_params = [entry for entry in entries if entry.tab != "Params"]
    candidates = non_params or list(entries)
    if len(candidates) > 1:
        keys = ", ".join(entry.key for entry in candidates)
        raise LookupError(f"Component name {name!r} is ambiguous; import one of: {keys}")
    return candidates[0].cls
