"""CombineData - Combine non-null items out of several inputs (Grasshopper "Combine Data")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class CombineData(Component):
    """Combine non-null items out of several inputs.

    Inputs:
        inputs: Data to combine (Grasshopper Input 0 / Input 1 [item]).

    Outputs:
        result: Resulting data with as few nulls as possible (Grasshopper Result).
        index: Index of input that was copied into result (Grasshopper Index).

    Notes:
        Grasshopper: Sets > List > Combine Data (Combine).
        pyhopper decisions: item-wise over every stream (longest list, last item repeated): the
        first non-null item wins and ``index`` names its stream; when every stream is null the
        result is a null item with index -1, exactly like Grasshopper.
    """

    display_name = "Combine Data"
    nickname = "Combine"
    gh_guid = "e7c80ff6-0299-4303-be36-3080977c14a1"

    inputs = [
        InputParam("inputs", None, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("result"),
        OutputParam("index", int),
    ]
    variadic_inputs = True

    def generate(self, inputs=None):
        for position, item in enumerate(inputs or []):
            if item is not None:
                return item, position
        return None, -1
