"""BlurNumbers - Blur a list of numbers by averaging neighbours (Grasshopper "Blur Numbers")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class BlurNumbers(Component):
    """Blur a list of numbers by averaging neighbours.

    Inputs:
        numbers: Numbers to blur (Grasshopper Numbers [list]).
        strength: Blurring strength (0=none, 1=full) (Grasshopper Strength [item]).
        iterations: Number of successive blurring iterations (Grasshopper Iterations [item]).
        lock: Lock first and last value (Grasshopper Lock [item]).
        wrap: Treat the list as a cyclical collection (Grasshopper Wrap [item]).

    Outputs:
        numbers: Blurred numbers (Grasshopper Numbers).

    Notes:
        Grasshopper: Maths > Util > Blur Numbers (NBlur).
        pyhopper decisions: Grasshopper-verified — every iteration replaces each number by
        ``(1 - strength) * value + strength * mean(neighbours)`` using the previous iteration's values;
        ends have one neighbour unless ``wrap`` closes the list, ``lock`` keeps the first and last
        values of an unwrapped list (a wrapped list has no ends), strengths outside [0, 1] extrapolate, zero iterations return the input and negative
        iterations raise ``ValueError``. Defaults: strength 0.5, one iteration, locked, unwrapped.
    """

    display_name = "Blur Numbers"
    nickname = "NBlur"
    gh_guid = "57e1d392-e3fb-4de9-be98-982854a92351"

    inputs = [
        InputParam("numbers", float, Access.LIST),
        InputParam("strength", float, Access.ITEM, default=0.5),
        InputParam("iterations", int, Access.ITEM, default=1),
        InputParam("lock", bool, Access.ITEM, default=True),
        InputParam("wrap", bool, Access.ITEM, default=False),
    ]
    outputs = [
        OutputParam("numbers", float, access=Access.LIST),
    ]

    def generate(self, numbers=None, strength=0.5, iterations=1, lock=True, wrap=False):
        values = [float(item) for item in (numbers or [])]
        rounds = int(iterations)
        if rounds < 0:
            raise ValueError("BlurNumbers needs a non-negative number of iterations")
        count = len(values)
        if count < 2:
            return values
        weight = float(strength)
        for _ in range(rounds):
            blurred = []
            for index, value in enumerate(values):
                neighbours = []
                if index > 0 or wrap:
                    neighbours.append(values[index - 1])
                if index < count - 1 or wrap:
                    neighbours.append(values[(index + 1) % count])
                if lock and not wrap and index in (0, count - 1):
                    blurred.append(value)
                else:
                    blurred.append((1.0 - weight) * value + weight * sum(neighbours) / len(neighbours))
            values = blurred
        return values
