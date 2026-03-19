from __future__ import annotations

from importlib import import_module
from inspect import getdoc, getmembers, isclass
from pathlib import Path
from typing import Any

from pyhopper.Core.Component import Component, InputParam, OutputParam


COMPONENTS_ROOT = Path(__file__).parent / "Components"


def _type_name(type_hint: type | None) -> str | None:
    if type_hint is None:
        return None
    return getattr(type_hint, "__name__", str(type_hint))


def _serialize_input(param: InputParam) -> dict[str, Any]:
    return {
        "name": param.name,
        "type": _type_name(param.type_hint),
        "access": param.access.value,
        "default": param.default,
        "optional": param.optional,
    }


def _serialize_output(param: OutputParam) -> dict[str, Any]:
    return {
        "name": param.name,
        "type": _type_name(param.type_hint),
    }


def _serialize_component(tab: str, category: str, component_cls: type[Component]) -> dict[str, Any]:
    inputs = [_serialize_input(param) for param in getattr(component_cls, "inputs", [])]
    outputs = [_serialize_output(param) for param in getattr(component_cls, "outputs", [])]
    frontend_preset = getattr(component_cls, "frontend_preset", None)
    frontend_config = getattr(component_cls, "frontend_config", None)
    variadic_inputs = bool(getattr(component_cls, "variadic_inputs", False))

    return {
        "component_key": f"{component_cls.__module__}.{component_cls.__name__}",
        "tab": tab,
        "category": category,
        "component": component_cls.__name__,
        "description": getdoc(component_cls) or "",
        "frontend_preset": frontend_preset,
        "frontend_config": frontend_config,
        "input_count": len(inputs),
        "output_count": len(outputs),
        "variadic_inputs": variadic_inputs,
        "inputs": inputs,
        "outputs": outputs,
    }


def list_components() -> list[dict[str, Any]]:
    components: list[dict[str, Any]] = []

    for src_path in sorted(COMPONENTS_ROOT.rglob("*.py")):
        if src_path.name.startswith("_"):
            continue

        rel_parts = src_path.relative_to(COMPONENTS_ROOT).with_suffix("").parts
        if not rel_parts:
            continue

        tab = rel_parts[0]
        category = "/".join(rel_parts[1:-1]) if len(rel_parts) > 2 else "General"
        module_name = ".".join(("pyhopper", "Components", *rel_parts))
        module = import_module(module_name)

        for _, member in getmembers(module, isclass):
            if member is Component:
                continue
            if not issubclass(member, Component):
                continue
            if member.__module__ != module.__name__:
                continue

            components.append(_serialize_component(tab, category, member))

    components.sort(key=lambda item: (item["tab"], item["category"], item["component"]))
    return components
