from __future__ import annotations

from importlib import import_module
from inspect import getdoc, getmembers, isclass
from pathlib import Path
from typing import Any

from pyhopper.Core.Component import Component, InputParam, OutputParam
from pyhopper.Core.TypeSystem import accepted_type_names, type_name


COMPONENTS_ROOT = Path(__file__).resolve().parents[1] / "Components"


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    to_json = getattr(value, "to_json", None)
    if callable(to_json):
        try:
            return _json_safe(to_json())
        except Exception:
            pass

    return repr(value)


def serialize_input(param: InputParam) -> dict[str, Any]:
    return {
        "name": param.name,
        "type": type_name(param.type_hint),
        "accepts": accepted_type_names(param.type_hint),
        "access": param.access.value,
        "default": _json_safe(param.default),
        "optional": param.optional,
    }


def serialize_output(param: OutputParam) -> dict[str, Any]:
    return {
        "name": param.name,
        "type": type_name(param.type_hint),
    }


def serialize_component(tab: str, category: str, component_cls: type[Component]) -> dict[str, Any]:
    inputs = [serialize_input(param) for param in getattr(component_cls, "inputs", [])]
    outputs = [serialize_output(param) for param in getattr(component_cls, "outputs", [])]
    settings_schema = getattr(component_cls, "settings_schema", None)
    variadic_inputs = bool(getattr(component_cls, "variadic_inputs", False))
    settings_defaults = {
        key: _json_safe(spec.get("default"))
        for key, spec in settings_schema.items()
        if isinstance(spec, dict) and "default" in spec
    } if isinstance(settings_schema, dict) else {}
    initial_settings = dict(settings_defaults)
    initial_values: dict[str, Any] = {}
    component_name = component_cls.__name__

    if component_name == "BooleanToggle":
        initial_values = {"value": bool(getattr(component_cls, "DEFAULT_VALUE", False))}
    elif component_name == "MDSlider":
        initial_values = {
            "x": float(getattr(component_cls, "DEFAULT_X", 0.5)),
            "y": float(getattr(component_cls, "DEFAULT_Y", 0.5)),
        }
    elif component_name == "GraphMapper":
        initial_values = dict(settings_defaults)
        initial_settings = {}
    elif component_name == "Panel":
        initial_values = {
            "text": "",
            "textAlign": "left",
            "multilineData": False,
        }
    elif component_name == "PointOnCurve":
        initial_values = {
            "parameter": settings_defaults.get("parameter", 0.5),
        }

    return {
        "component_key": f"{component_cls.__module__}.{component_cls.__name__}",
        "tab": tab,
        "category": category,
        "component": component_cls.__name__,
        "description": getdoc(component_cls) or "",
        "settings_schema": _json_safe(settings_schema if isinstance(settings_schema, dict) else {}),
        "settings_defaults": settings_defaults,
        "initial_settings": _json_safe(initial_settings),
        "initial_values": _json_safe(initial_values),
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

            components.append(serialize_component(tab, category, member))

    components.sort(key=lambda item: (item["tab"], item["category"], item["component"]))
    return components
