"""Naming rules that turn Grasshopper names into pyhopper class and port names.

This module is the single source of truth used by the scaffold generator
(``scripts/new_component.py``) and by the metadata/naming tests, so names
cannot drift between contributors. The rules are documented in
``CONTRACTS/NEW_COMPONENT.md``; the special cases live in the override tables.
"""

from __future__ import annotations

import keyword
import re

# (tab, subcategory, Grasshopper name) -> class name. Only for cases the rules cannot derive.
NAME_OVERRIDES: dict[tuple[str, str, str], str] = {
    ("Sets", "Sets", "Set Difference (S)"): "SymmetricDifference",
    ("Maths", "Util", "Natural logarithm"): "EulerNumber",      # the constant e (× factor), not the log
    ("Surface", "Util", "Flip"): "FlipSurface",                 # symmetry with FlipCurve / FlipPlane / FlipMatrix
    ("Params", "Geometry", "Circular Arc"): "Arc",              # containers are named after their atom
    ("Vector", "Point", "Deconstruct"): "DeconstructPoint",     # existing component
    ("Curve", "Spline", "PolyLine"): "Polyline",                # existing component
    # cross-tab collisions (class names must be unique outside Params)
    ("Curve", "Analysis", "Extremes"): "CurveExtremes",         # Maths › Util › Extremes keeps the bare name
    ("Curve", "Division", "Contour (ex)"): "CurveContourEx",    # Intersect › Mathematical › Contour (ex) keeps ContourEx
    ("Intersect", "Mathematical", "Mesh | Plane"): "MeshPlaneSection",  # Mesh › Primitive › Mesh Plane keeps MeshPlane
}

# Grid components carry the Grid suffix (GH nicknames RecGrid/SqGrid/HexGrid/TriGrid/RadGrid do too).
GRID_SUFFIX_NAMES = {"Rectangular", "Square", "Hexagonal", "Triangular", "Radial"}

LEADING_DIGITS = {"1": "One", "2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}

# (component Grasshopper name, port Grasshopper name) -> port name.
PORT_OVERRIDES: dict[tuple[str, str], str] = {
    ("Larger Than", "… or Equal to"): "larger_or_equal",
    ("Larger Than", "Larger than"): "larger_than",
    ("Smaller Than", "… or Equal to"): "smaller_or_equal",
    ("Smaller Than", "Smaller than"): "smaller_than",
    ("Extremes", "Mininum"): "minimum",                         # GH typo
    ("Length Parameter", "Length"): "length_before",            # first output; the second is mapped by position
    ("Bounding Box", "Box"): "box",                             # first output; plane-oriented box mapped by position
    ("Extrude Linear", "Orientation (P)"): "profile_orientation",
    ("Extrude Linear", "Orientation (A)"): "axis_orientation",
    ("Match Text", "RegEx"): "regex",
    ("Set Difference (S)", "ExDifference"): "symmetric_difference",
    ("Sort List", "Values A"): "values",                        # variadic collapse
    # "output" shadows ComponentResult.output(); the constants follow the Maths "Result" convention
    ("Pi", "Output"): "result",
    ("Golden Ratio", "Output"): "result",
    ("Epsilon", "Output"): "result",
    ("Natural logarithm", "Output"): "result",
}

# Output ports whose Grasshopper name would collide with (or mislead next to) an input of the same name.
OUTPUT_PORT_OVERRIDES: dict[tuple[str, str], str] = {
    ("Plane Surface", "Plane"): "surface",                      # the input plane keeps "plane"
}

# Second occurrence of a duplicated GH output name (mapped by position when names repeat).
DUPLICATE_OUTPUT_OVERRIDES: dict[tuple[str, str], str] = {
    ("Length Parameter", "Length"): "length_after",
    ("Bounding Box", "Box"): "plane_box",
}

# Python keywords get a type word appended; extend as new ports need it.
KEYWORD_SUFFIX: dict[str, str] = {
    "from": "from_vector",
    "to": "to_vector",
    "in": "in_value",
    "is": "is_value",
    "not": "not_value",
    "and": "and_value",
    "or": "or_value",
    "if": "if_value",
    "else": "else_value",
    "for": "for_value",
    "while": "while_value",
    "with": "with_value",
    "as": "as_value",
    "def": "def_value",
    "class": "class_value",
    "return": "return_value",
    "import": "import_value",
    "pass": "pass_value",
    "lambda": "lambda_value",
    "yield": "yield_value",
}

# Variadic stream ports: GH numbers them ("Stream 0", "Data 1"); pyhopper collapses them into one plural port.
VARIADIC_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^Stream \d+$"), "streams"),
    (re.compile(r"^Data \d+$"), "data"),
    (re.compile(r"^Input \d+$"), "inputs"),
    (re.compile(r"^Branch \{0;\d+\}$"), "branches"),
    (re.compile(r"^Values [A-Z]$"), "values"),
)


def _capitalize_token(token: str) -> str:
    return token[0].upper() + token[1:] if token[0].isalpha() else token


def _tokens(text: str) -> list[str]:
    return [token for token in re.split(r"[^A-Za-z0-9]+", text) if token]


def class_name_for(gh_name: str, tab: str | None = None, sub: str | None = None) -> str:
    """Derive the pyhopper class name for a Grasshopper component name.

    Rules: ``|`` is dropped, ``+`` becomes ``Plus``, a parenthesised qualifier is
    appended, ``²`` → ``2``, other punctuation separates tokens, tokens keep
    their Grasshopper capitalisation except for an upper-cased first letter, a
    leading digit is spelled out, and Vector › Grid single-word names gain the
    ``Grid`` suffix. Overrides win.
    """
    if tab is not None and sub is not None and (tab, sub, gh_name) in NAME_OVERRIDES:
        return NAME_OVERRIDES[(tab, sub, gh_name)]

    name = gh_name.strip()
    qualifier = ""
    match = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", name)
    if match:
        name, qualifier = match.group(1), match.group(2)
    name = name.replace("²", "2").replace("|", " ").replace("+", " Plus ")

    tokens = _tokens(name)
    result = "".join(_capitalize_token(token) for token in tokens)
    if qualifier:
        result += "".join(_capitalize_token(token) for token in _tokens(qualifier))
    if result and result[0].isdigit():
        result = LEADING_DIGITS[result[0]] + result[1:]
    if tab == "Vector" and sub == "Grid" and len(tokens) == 1 and tokens[0] in GRID_SUFFIX_NAMES:
        result += "Grid"
    return result


def variadic_port_name(gh_port_name: str) -> str | None:
    """Plural port name when *gh_port_name* is one of Grasshopper's numbered stream ports."""
    for pattern, plural in VARIADIC_PATTERNS:
        if pattern.match(gh_port_name):
            return plural
    return None


def port_name_for(gh_port_name: str, gh_component_name: str | None = None, *, duplicate: bool = False, output: bool = False) -> str:
    """Derive a snake_case pyhopper port name from a Grasshopper port name.

    ``output`` selects the output-only overrides (Plane Surface's "Plane" output
    is the surface); ``duplicate`` selects the second mapping when a component
    repeats an output name (Length Parameter, Bounding Box). Overrides win;
    numbered stream ports collapse to their plural variadic name.
    """
    if gh_component_name is not None:
        if duplicate and (gh_component_name, gh_port_name) in DUPLICATE_OUTPUT_OVERRIDES:
            return DUPLICATE_OUTPUT_OVERRIDES[(gh_component_name, gh_port_name)]
        if output and (gh_component_name, gh_port_name) in OUTPUT_PORT_OVERRIDES:
            return OUTPUT_PORT_OVERRIDES[(gh_component_name, gh_port_name)]
        if (gh_component_name, gh_port_name) in PORT_OVERRIDES:
            return PORT_OVERRIDES[(gh_component_name, gh_port_name)]
    plural = variadic_port_name(gh_port_name)
    if plural:
        return plural

    text = gh_port_name.replace("²", "2").strip()
    text = re.sub(r"\?$", "", text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)          # CamelCase → words
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    if not text:
        raise ValueError(f"Cannot derive a port name from {gh_port_name!r}")
    if text[0].isdigit():
        text = "_" + text
    if keyword.iskeyword(text):
        text = KEYWORD_SUFFIX.get(text, f"{text}_value")
    return text


# Grasshopper parameter type name -> pyhopper type-hint expression (as source text for the scaffold).
GH_TYPE_HINTS: dict[str, str] = {
    "Number": "float",
    "Integer": "int",
    "Boolean": "bool",
    "Text": "str",
    "Culture": "str",
    "Generic Data": "None",
    "Point": "AtomicPoint",
    "Vector": "AtomicVector",
    "Plane": "AtomicPlane",
    "Line": "AtomicLine",
    "Circle": "AtomicCircle",
    "Arc": "AtomicArc",
    "Rectangle": "AtomicRectangle",
    "Box": "AtomicBox",
    "Mesh": "AtomicMesh",
    "Transform": "AtomicTransform",
    "Brep": "AtomicBrep",
    "Domain": "AtomicInterval",
    "Path": "Path",
    "Curve": "CURVE",
    "Surface": "SURFACE",
    "Geometry": "GEOMETRY",
}
