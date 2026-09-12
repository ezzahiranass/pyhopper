"""CrossReference - Cross Reference data from multiple lists (Grasshopper "Cross Reference")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class CrossReference(Component):
    """Cross Reference data from multiple lists.

    Inputs:
        list_a: List (A) to operate on (Grasshopper List (A) [list]).
        list_b: List (B) to operate on (Grasshopper List (B) [list]).

    Outputs:
        list_a: Adjusted list (A) (Grasshopper List (A)).
        list_b: Adjusted list (B) (Grasshopper List (B)).

    Notes:
        Grasshopper: Sets > List > Cross Reference (CrossRef).
        pyhopper decisions: Grasshopper's default "Holistic" mode only: every combination, A
        cycling fastest (``A0 B0, A1 B0, …, A0 B1, …``); a missing list leaves both outputs empty
        except that a lone list passes through unchanged, as Grasshopper does.
    """

    display_name = "Cross Reference"
    nickname = "CrossRef"
    gh_guid = "36947590-f0cb-4807-a8f9-9c90c9b20621"

    inputs = [
        InputParam("list_a", None, Access.LIST, optional=True),
        InputParam("list_b", None, Access.LIST, optional=True),
    ]
    outputs = [
        OutputParam("list_a", access=Access.LIST),
        OutputParam("list_b", access=Access.LIST),
    ]

    def generate(self, list_a=None, list_b=None):
        a, b = list(list_a or []), list(list_b or [])
        if not a or not b:
            return a, b
        return [item for _ in b for item in a], [item for item in b for _ in a]
