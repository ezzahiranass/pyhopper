"""Probe a Grasshopper *parameter* (Suirify) by feeding it from a Data container source.

Run:  rhino-test\\.venv\\Scripts\\python rhino-test\\gh_probe_param.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from oracle import gh_headless as H  # noqa: E402
from tests.support.trees import tree as T  # noqa: E402

SUIRIFY = "5d4e1eeb-482e-42a7-aa2f-e5deb8a1018e"
DATA = "8ec86459-bf01-4409-baee-174d0d2b13d0"


def invoke(obj, name, *args):
    """Call a method on the concrete .NET type by name (the proxy hands back interface-typed objects)."""
    import System  # type: ignore

    for method in obj.GetType().GetMethods():
        if method.Name == name and method.GetParameters().Length == len(args):
            return method.Invoke(obj, System.Array[System.Object](list(args)) if args else None)
    raise AttributeError(name)


def prop(obj, name):
    return obj.GetType().GetProperty(name).GetValue(obj, None)


def solve_param(guid: str, source_tree):
    Grasshopper = H.load_grasshopper()
    import System  # type: ignore

    doc = H._document
    source = Grasshopper.Instances.ComponentServer.EmitObjectProxy(System.Guid(DATA)).CreateInstance()
    target = Grasshopper.Instances.ComponentServer.EmitObjectProxy(System.Guid(guid)).CreateInstance()
    doc.AddObject(source, False)
    doc.AddObject(target, False)
    try:
        for branch_path, branch in source_tree.branches():
            values = System.Collections.Generic.List[System.Object]()
            for item in branch:
                values.Add(H.to_net(item))
            invoke(source, "AddVolatileDataList", H._gh_path(branch_path), values)
        invoke(target, "AddSource", source)
        H._call(target, "CollectData")
        H._call(target, "ComputeData")
        data = prop(target, "VolatileData")
        branches = {}
        for gh_path in data.Paths:
            branches[H._path_from_gh(gh_path)] = [H.to_python(goo) for goo in data.get_Branch(gh_path)]
        return branches
    finally:
        doc.RemoveObject(target, False)
        doc.RemoveObject(source, False)


PROBES = [
    ("single items per branch", T({"0;0": [1], "0;1": [2], "0;2": [3]})),
    ("single items deep paths", T({"0;0;0": [1], "0;0;1": [2]})),
    ("one branch many items", T({"0;0": [1, 2, 3]})),
    ("one branch deep", T({"5;2;1": [1, 2, 3]})),
    ("mixed counts", T({"0;0": [1, 2], "0;1": [3]})),
    ("two branches lists", T({"0;0": [1, 2], "0;1": [3, 4]})),
    ("ragged with empty", T({"0;0": [1, 2], "0;1": [], "0;2": [3]})),
    ("flat list", T([1, 2, 3])),
    ("single item", T([7])),
    ("shared prefix long", T({"2;3;0": [1], "2;3;1": [2, 3]})),
    ("two lists no shared prefix", T({"1": [1, 2], "3": [4]})),
    ("all singletons no shared prefix", T({"1": [1], "3": [2]})),
]

for label, source_tree in PROBES:
    try:
        result = solve_param(SUIRIFY, source_tree)
    except Exception as exc:
        print(f"## {label}\n  ERROR {exc!r}")
        continue
    body = "; ".join(f"{path}: {items!r}" for path, items in result.items()) or "<empty>"
    print(f"## {label}\n  {body}")
