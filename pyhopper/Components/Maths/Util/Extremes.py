"""Extremes - Find the extremes in a list of values (Grasshopper "Extremes")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Core.Atoms import AtomicVector
from pyhopper.Utils.Text import format_number
from pyhopper.Utils.Vectors import length

from .._arith import is_number


def extreme_key(value):
    """Sort key Grasshopper's Extremes uses: numbers and booleans as numbers, vectors by length, text as text."""
    if isinstance(value, bool) or is_number(value):
        return float(value)
    if isinstance(value, str):
        return value
    if isinstance(value, AtomicVector):
        return length(value)
    raise TypeError("Extremes handles booleans, numbers, text and vectors only")


class Extremes(Component):
    """Find the extremes in a list of values.

    Inputs:
        a: Value for comparison (Grasshopper A [item]).
        b: Value for comparison (Grasshopper B [item]).

    Outputs:
        minimum: Lowest of all values (Grasshopper Mininum).
        maximum: Highest of all values (Grasshopper Maximum).

    Notes:
        Grasshopper: Maths > Util > Extremes (Extrz).
        pyhopper decisions: item-wise minimum and maximum of A and B (longest list, one missing
        input compares with itself, both missing emit nothing); numbers, booleans and text compare
        natively, vectors by length, and mixing text with numbers compares everything as text —
        all Grasshopper-verified. Points and other atoms raise ``TypeError``.
    """

    display_name = "Extremes"
    nickname = "Extrz"
    gh_guid = "37084b3f-2b66-4f3a-9737-80d0b0b7f0cb"

    inputs = [
        InputParam("a", None, Access.ITEM, optional=True),
        InputParam("b", None, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("minimum"),
        OutputParam("maximum"),
    ]

    def generate(self, a=None, b=None):
        present = [value for value in (a, b) if value is not None]
        if not present:
            return Component.NO_OUTPUT, Component.NO_OUTPUT
        keys = [extreme_key(value) for value in present]
        if any(isinstance(key, str) for key in keys):
            # Grasshopper: "since you are comparing text and non-text, all data will be treated as text"
            present = [value if isinstance(value, str) else format_number(value) for value in present]
            keys = list(present)
        low = min(range(len(present)), key=lambda index: keys[index])
        high = max(range(len(present)), key=lambda index: keys[index])
        return present[low], present[high]
