"""Panel - Display and pass through arbitrary DataTree content."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Panel(Component):
    """Display a tree's contents while passing its data through unchanged.

    Grasshopper's Panel is primarily a debugging and inspection parameter. In
    pyhopper it keeps the standard component solve model: one input named
    ``data``, one output named ``data``, and a branch-wise pass-through
    ``generate()`` implementation. The web frontend may use the declarative
    ``frontend_preset`` metadata to render the incoming tree in a readable node
    view without changing the backend definition.
    """

    inputs = [InputParam("data", None, Access.LIST, default=[])]
    outputs = [OutputParam("data")]
    frontend_preset = "panel"

    def generate(self, data=None):
        """Return the matched branch contents unchanged."""
        return [] if data is None else data
