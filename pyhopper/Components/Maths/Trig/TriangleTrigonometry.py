"""TriangleTrigonometry - Generic triangle trigonometry (Grasshopper "Triangle Trigonometry")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._triangles import solve_triangle


class TriangleTrigonometry(Component):
    """Generic triangle trigonometry.

    Inputs:
        alpha: Optional alpha angle (Grasshopper Alpha [item]).
        beta: Optional beta angle (Grasshopper Beta [item]).
        gamma: Optional gamma angle (Grasshopper Gamma [item]).
        a_length: Optional length of A edge (opposite alpha) (Grasshopper A length [item]).
        b_length: Optional length of B edge (opposite beta) (Grasshopper B length [item]).
        c_length: Optional length of C edge (opposite gamma) (Grasshopper C length [item]).

    Outputs:
        alpha: Computed alpha angle (Grasshopper Alpha).
        beta: Computed beta angle (Grasshopper Beta).
        gamma: Computed gamma angle (Grasshopper Gamma).
        a_length: Computed length of A edge (Grasshopper A length).
        b_length: Computed length of B edge (Grasshopper B length).
        c_length: Computed length of C edge (Grasshopper C length).

    Notes:
        Grasshopper: Maths > Trig > Triangle Trigonometry (Trig).
        pyhopper decisions: Grasshopper-verified — edge A is opposite alpha, B opposite beta, C
        opposite gamma; given values are echoed, unknowns are filled from two angles, three sides (law
        of cosines), two sides with the included angle (law of cosines) or a side with its opposite
        angle (law of sines, acute solution for the ambiguous case), and whatever stays unknown is
        emitted as nothing. Impossible data (angles not summing to pi, a zero edge, an edge longer than
        the other two combined, no law-of-sines solution) raises ``ValueError`` where Grasshopper
        reports an error or never finishes.
    """

    display_name = "Triangle Trigonometry"
    nickname = "Trig"
    gh_guid = "92af1a02-9b87-43a0-8c45-0ce1b81555ec"

    inputs = [
        InputParam("alpha", float, Access.ITEM, optional=True),
        InputParam("beta", float, Access.ITEM, optional=True),
        InputParam("gamma", float, Access.ITEM, optional=True),
        InputParam("a_length", float, Access.ITEM, optional=True),
        InputParam("b_length", float, Access.ITEM, optional=True),
        InputParam("c_length", float, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("alpha", float),
        OutputParam("beta", float),
        OutputParam("gamma", float),
        OutputParam("a_length", float),
        OutputParam("b_length", float),
        OutputParam("c_length", float),
    ]

    def generate(self, alpha=None, beta=None, gamma=None, a_length=None, b_length=None, c_length=None):
        angles, sides = solve_triangle([alpha, beta, gamma], [a_length, b_length, c_length])
        return tuple(Component.NO_OUTPUT if value is None else value for value in (*angles, *sides))
