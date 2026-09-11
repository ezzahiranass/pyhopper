"""Naming rules: derivable class names, global uniqueness outside Params, port-name rules."""

from __future__ import annotations

import json
import keyword
import unittest
from collections import Counter
from pathlib import Path

from pyhopper.Graph.catalog import list_components
from pyhopper.Graph.naming import class_name_for, port_name_for

PLAN = Path(__file__).resolve().parents[1] / "rhino-test" / "component_roadmap_plan.json"


class ClassNameRuleTests(unittest.TestCase):
    def test_documented_examples(self) -> None:
        cases = {
            ("Line | Line", "Intersect", "Mathematical"): "LineLine",
            ("Plane | Plane | Plane", "Intersect", "Mathematical"): "PlanePlanePlane",
            ("Line + Pt", "Vector", "Plane"): "LinePlusPt",
            ("Tangent Lines (Ex)", "Curve", "Primitive"): "TangentLinesEx",
            ("Interpolate (t)", "Curve", "Spline"): "InterpolateT",
            ("Contour (ex)", "Intersect", "Mathematical"): "ContourEx",
            ("Colour RGB (f)", "Display", "Colour"): "ColourRGBF",
            ("Domain²", "Params", "Primitive"): "Domain2",
            ("Pick'n'Choose", "Sets", "List"): "PickNChoose",
            ("Key/Value Search", "Sets", "Sets"): "KeyValueSearch",
            ("Power of 2", "Maths", "Polynomials"): "PowerOf2",
            ("Rectangle 2Pt", "Curve", "Primitive"): "Rectangle2Pt",
            ("Sphere 4Pt", "Surface", "Primitive"): "Sphere4Pt",
            ("4Point Surface", "Surface", "Freeform"): "FourPointSurface",
            ("Nurbs Curve PWK", "Curve", "Spline"): "NurbsCurvePWK",
            ("SubSet", "Sets", "Sets"): "SubSet",
            ("Carthesian Product", "Sets", "Sets"): "CarthesianProduct",
            ("Rectangular", "Vector", "Grid"): "RectangularGrid",
            ("Populate 2D", "Vector", "Grid"): "Populate2D",
            ("Set Difference (S)", "Sets", "Sets"): "SymmetricDifference",
            ("Natural logarithm", "Maths", "Util"): "EulerNumber",
            ("Natural logarithm", "Maths", "Polynomials"): "NaturalLogarithm",
            ("Flip", "Surface", "Util"): "FlipSurface",
            ("Circular Arc", "Params", "Geometry"): "Arc",
            ("Extremes", "Curve", "Analysis"): "CurveExtremes",
            ("Mesh | Plane", "Intersect", "Mathematical"): "MeshPlaneSection",
            ("Circle CNR", "Curve", "Primitive"): "CircleCNR",
            ("MD Slider", "Params", "Input"): "MDSlider",
        }
        for (name, tab, sub), expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(class_name_for(name, tab, sub), expected)

    @unittest.skipUnless(PLAN.exists(), "roadmap plan not available")
    def test_every_tier_one_and_two_candidate_gets_a_unique_identifier(self) -> None:
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        names: Counter = Counter()
        for candidate in plan["candidates"]:
            if candidate["tier"] > 2:
                continue
            name = class_name_for(candidate["name"], candidate["tab"], candidate["sub"])
            self.assertTrue(name.isidentifier(), f"{candidate['name']!r} -> {name!r}")
            self.assertFalse(keyword.iskeyword(name))
            names[(candidate["tab"] == "Params", name)] += 1
        duplicates = {key: count for key, count in names.items() if count > 1}
        self.assertEqual(duplicates, {}, "class names must be unique (Params containers excepted)")


class ExistingCatalogNamingTests(unittest.TestCase):
    def test_class_names_are_unique_outside_params(self) -> None:
        counts = Counter(entry["component"] for entry in list_components() if entry["tab"] != "Params")
        grandfathered = {"Rotate", "Circle", "Line", "Cylinder"}  # pre-existing duplicates across tabs
        duplicates = {name: count for name, count in counts.items() if count > 1 and name not in grandfathered}
        self.assertEqual(duplicates, {})


class PortNameRuleTests(unittest.TestCase):
    def test_port_names(self) -> None:
        cases = {
            "X coordinate": "x_coordinate",
            "Values A": "values",
            "List (A)": "list_a",
            "Center(V)": "center_v",
            "Hull(z)": "hull_z",
            "CP Index": "cp_index",
            "Z-Axis": "z_axis",
            "Reparameterize?": "reparameterize",
            "KnotStyle": "knot_style",
            "MinEdge": "min_edge",
            "From": "from_vector",
            "Stream 3": "streams",
            "Data 1": "data",
            "Branch {0;2}": "branches",
            "Domain²": "domain2",
        }
        for gh_name, expected in cases.items():
            with self.subTest(port=gh_name):
                self.assertEqual(port_name_for(gh_name), expected)

    def test_component_specific_overrides(self) -> None:
        self.assertEqual(port_name_for("Mininum", "Extremes"), "minimum")
        self.assertEqual(port_name_for("Length", "Length Parameter"), "length_before")
        self.assertEqual(port_name_for("Length", "Length Parameter", duplicate=True), "length_after")
        self.assertEqual(port_name_for("Box", "Bounding Box", duplicate=True), "plane_box")
        self.assertEqual(port_name_for("RegEx", "Match Text"), "regex")


if __name__ == "__main__":
    unittest.main()
