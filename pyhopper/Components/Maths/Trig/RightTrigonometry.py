"""RightTrigonometry - Right triangle trigonometry (Grasshopper "Right Trigonometry")."""

from __future__ import annotations

import math

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam

from ._triangles import solve_triangle


class RightTrigonometry(Component):
    """Right triangle trigonometry.

    Inputs:
        alpha: Optional alpha angle (Grasshopper Alpha [item]).
        beta: Optional beta angle (Grasshopper Beta [item]).
        p_length: Optional length of P edge (Grasshopper P length [item]).
        q_length: Optional length of Q edge (Grasshopper Q length [item]).
        r_length: Optional length of R edge (Grasshopper R length [item]).

    Outputs:
        alpha: Computed alpha angle (Grasshopper Alpha).
        beta: Computed beta angle (Grasshopper Beta).
        p_length: Computed length of P edge (Grasshopper P length).
        q_length: Computed length of Q edge (Grasshopper Q length).
        r_length: Computed length of R edge (Grasshopper R length).

    Notes:
        Grasshopper: Maths > Trig > Right Trigonometry (RTrig).
        pyhopper decisions: Grasshopper-verified — P and Q are the legs (P opposite beta, Q opposite
        alpha), R the hypotenuse; the general triangle solver runs with the right angle preset, so
        given values are echoed, unknowns are filled from two angles, three sides (law of cosines), two
        sides with the included angle (law of cosines) or a side with its opposite angle (law of
        sines), and whatever stays unknown is emitted as nothing. Impossible data raises ``ValueError``
        (Grasshopper reports an error or never finishes).
    """

    display_name = "Right Trigonometry"
    nickname = "RTrig"
    gh_guid = "e75d4624-8ee2-4067-ac8d-c56bdc901d83"

    inputs = [
        InputParam("alpha", float, Access.ITEM, optional=True),
        InputParam("beta", float, Access.ITEM, optional=True),
        InputParam("p_length", float, Access.ITEM, optional=True),
        InputParam("q_length", float, Access.ITEM, optional=True),
        InputParam("r_length", float, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("alpha", float),
        OutputParam("beta", float),
        OutputParam("p_length", float),
        OutputParam("q_length", float),
        OutputParam("r_length", float),
    ]

    def generate(self, alpha=None, beta=None, p_length=None, q_length=None, r_length=None):
        angles, sides = solve_triangle([alpha, beta, math.pi / 2.0], [q_length, p_length, r_length], component="RightTrigonometry")
        return tuple(Component.NO_OUTPUT if value is None else value for value in (angles[0], angles[1], sides[1], sides[0], sides[2]))
