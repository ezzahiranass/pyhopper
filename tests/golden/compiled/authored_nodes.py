from __future__ import annotations

from pyhopper.Components.Curve.Analysis.PointOnCurve import PointOnCurve
from pyhopper.Components.Curve.Division.DivideCurve import DivideCurve
from pyhopper.Components.Maths.Series import Series
from pyhopper.Components.Params.Input.GraphMapper import map_graph_tree
from pyhopper.Components.Params.Input.NumberSlider import NumberSlider
from pyhopper.Components.Params.Input.Panel import Panel
from pyhopper.Components.Params.Input.Panel import parse_panel_lines
from pyhopper.Components.Params.Input.Panel import parse_panel_text
from pyhopper.Components.Sets.Tree.Merge import Merge
from pyhopper.Core.Atoms import AtomicTransform
from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Core.Atoms import atom_from_json
from pyhopper.Core.DataTree import DataTree
from pyhopper.Utils.Curves import reparametrize_tree
from pyhopper.Utils.Transforms import apply_transform

def build_graph_node_outputs():
    node_000_panel = DataTree.from_item(parse_panel_text('25'))
    node_001_object_reference = DataTree.from_item(apply_transform(AtomicTransform.from_json({'type': 'Transform', 'matrix': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]}), atom_from_json({'type': 'Line', 'start': {'type': 'Point3d', 'x': 0.0, 'y': 0.0, 'z': 0.0}, 'end': {'type': 'Point3d', 'x': 8.0, 'y': 0.0, 'z': 0.0}})))
    node_002_point_on_curve = PointOnCurve(curve=node_001_object_reference, parameter=0.25)
    node_003_point_on_curve = PointOnCurve(curve=node_001_object_reference, parameter=0.5)
    node_004_mdslider = DataTree.from_item(AtomicVector(0.2, 0.8, 0.0))
    node_005_panel = DataTree.from_list(parse_panel_lines('25\n16\ntrue\nlabel'))
    node_006_panel = DataTree.from_item(parse_panel_text('12\nfixed value'))
    node_007_series = Series()
    node_007_series__series = node_007_series.graft()
    node_008_number_slider = NumberSlider(_settings={'value': 4.74, 'min': 0.0, 'max': 10.0, 'decimals': 2, 'rounding': 'integer'})
    node_009_divide_curve = DivideCurve(curve=reparametrize_tree(node_001_object_reference), count=node_008_number_slider)
    node_010_graph_mapper = map_graph_tree(node_008_number_slider, {'graphType': 'linear', 'xMin': 0.0, 'xMax': 1.0, 'yMin': 10.0, 'yMax': 20.0, 'controlY1': 0.15, 'controlY2': 0.85})
    node_011_number_slider = NumberSlider(_settings={'value': 0.25})
    node_012_number_slider = NumberSlider(_settings={})
    node_013_boolean_toggle = DataTree.from_item(True)
    node_014_boolean_toggle = DataTree.from_item(False)
    node_015_panel = Panel(data=node_010_graph_mapper)
    return {
        'integer-panel': node_000_panel,
        'line-reference': node_001_object_reference,
        'curve-point': node_002_point_on_curve,
        'curve-point-default': node_003_point_on_curve,
        'md': node_004_mdslider,
        'multiline-panel': node_005_panel,
        'panel': node_006_panel,
        'series': node_007_series__series,
        'slider': node_008_number_slider,
        'divide': node_009_divide_curve,
        'mapper': node_010_graph_mapper,
        'slider-legacy': node_011_number_slider,
        'slider-plain': node_012_number_slider,
        'toggle': node_013_boolean_toggle,
        'toggle-default': node_014_boolean_toggle,
        'viewer': node_015_panel,
    }

def build_graph_preview_outputs():
    node_outputs = build_graph_node_outputs()
    return {
        'integer-panel': node_outputs['integer-panel'],
        'line-reference': node_outputs['line-reference'],
        'curve-point': node_outputs['curve-point'],
        'curve-point-default': node_outputs['curve-point-default'],
        'md': node_outputs['md'],
        'multiline-panel': node_outputs['multiline-panel'],
        'panel': node_outputs['panel'],
        'series': node_outputs['series'],
        'slider': node_outputs['slider'],
        'divide': node_outputs['divide'],
        'mapper': node_outputs['mapper'],
        'slider-legacy': node_outputs['slider-legacy'],
        'slider-plain': node_outputs['slider-plain'],
        'toggle': node_outputs['toggle'],
        'toggle-default': node_outputs['toggle-default'],
        'viewer': node_outputs['viewer'],
    }

def build_graph_definition():
    preview_outputs = build_graph_preview_outputs()
    preview_values = list(preview_outputs.values())
    if len(preview_values) == 1:
        return preview_values[0]
    return Merge(*preview_values)
