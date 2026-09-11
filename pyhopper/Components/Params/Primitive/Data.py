"""Data - Contains a collection of generic data (Grasshopper "Data")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Data(Component):
    """Contains a collection of generic data.

    Inputs:
        data: Any value; passes through untouched (Grasshopper Data [item]).

    Outputs:
        data: The same value (Grasshopper Data).

    Notes:
        Grasshopper: Params > Primitive > Data (Data).
        pyhopper decisions: containers are components with one input and one output of the same name,
        like ``Number`` and ``Text``; any value passes through unchanged.
    """

    display_name = "Data"
    nickname = "Data"
    gh_guid = "8ec86459-bf01-4409-baee-174d0d2b13d0"

    inputs = [InputParam("data", None, Access.ITEM)]
    outputs = [OutputParam("data")]

    def generate(self, data=None):
        return data
