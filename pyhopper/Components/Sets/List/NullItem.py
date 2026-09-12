"""NullItem - Test a data item for null or invalidity (Grasshopper "Null Item")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import math


class NullItem(Component):
    """Test a data item for null or invalidity.

    Inputs:
        item: Item to test (Grasshopper Item [item]).

    Outputs:
        null_flags: True if item is Null. (Grasshopper Null Flags).
        invalid_flags: True if item is Invalid or Null. (Grasshopper Invalid Flags).
        description: A textual description of the object state. (Grasshopper Description).

    Notes:
        Grasshopper: Sets > List > Null Item (Null).
        pyhopper decisions: ``null_flags`` marks missing items, ``invalid_flags`` marks missing
        items and non-finite numbers (Grasshopper's invalid data); descriptions follow
        Grasshopper's wording ("Data does not exist", "Number is equal to the NaN constant.",
        empty for valid data).
    """

    display_name = "Null Item"
    nickname = "Null"
    gh_guid = "c74efd0e-7fe3-4c2d-8c9d-295c5672fb13"

    inputs = [
        InputParam("item", None, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("null_flags", bool),
        OutputParam("invalid_flags", bool),
        OutputParam("description", str),
    ]

    def generate(self, item=None):
        if item is None:
            return True, True, "Data does not exist"
        if isinstance(item, float) and not math.isfinite(item):
            return False, True, "Number is equal to the NaN constant." if math.isnan(item) else "Number is not finite."
        return False, False, """"""
