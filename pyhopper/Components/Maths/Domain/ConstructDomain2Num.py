"""ConstructDomain2Num - Create a two-dimensinal domain from four numbers (Grasshopper "Construct Domain²")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicInterval, AtomicInterval2
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ConstructDomain2Num(Component):
    """Create a two-dimensinal domain from four numbers.

    Inputs:
        u_min: Lower limit of domain in {u} direction (Grasshopper U min [item]).
        u_max: Upper limit of domain in {u} direction (Grasshopper U max [item]).
        v_min: Lower limit of domain in {v} direction (Grasshopper V min [item]).
        v_max: Upper limit of domain in {v} direction (Grasshopper V max [item]).

    Outputs:
        domain: Two dimensional numeric domain of {u} and {v} (Grasshopper 2D Domain).

    Notes:
        Grasshopper: Maths > Domain > Construct Domain² (Dom²Num).
        pyhopper decisions: none; the numbers are kept as given (a maximum below its minimum makes a
        reversed domain, as in Grasshopper). Grasshopper defaults 0, 1, 0, 1.
    """

    display_name = "Construct Domain²"
    nickname = "Dom²Num"
    gh_guid = "9083b87f-a98c-4e41-9591-077ae4220b19"

    inputs = [
        InputParam("u_min", float, Access.ITEM, default=0.0),
        InputParam("u_max", float, Access.ITEM, default=1.0),
        InputParam("v_min", float, Access.ITEM, default=0.0),
        InputParam("v_max", float, Access.ITEM, default=1.0),
    ]
    outputs = [
        OutputParam("domain", AtomicInterval2),
    ]

    def generate(self, u_min=0.0, u_max=1.0, v_min=0.0, v_max=1.0):
        return AtomicInterval2(AtomicInterval(float(u_min), float(u_max)), AtomicInterval(float(v_min), float(v_max)))
