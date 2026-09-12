"""Format - Format some data using placeholders and formatting tags (Grasshopper "Format")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.TextFormat import format_composite


class Format(Component):
    """Format some data using placeholders and formatting tags.

    Inputs:
        format: Text format (Grasshopper Format [item]).
        culture: Formatting culture (Grasshopper Culture [item]).
        data: Data to insert at {0} placeholders (Grasshopper Data 0 / Data 1 [item]).

    Outputs:
        text: Formatted text (Grasshopper Text).

    Notes:
        Grasshopper: Sets > Text > Format (Format).
        pyhopper decisions: .NET composite formatting (``Utils/TextFormat.py``): ``{0}``, alignment
        ``{0,8}``, the standard numeric formats D/E/F/G/N/P/X/R, custom pictures such as ``0.00``,
        ``#,##0.###``, ``0%`` and ``0.0;(0.0)``, and ``{{ }}`` escapes — all Grasshopper-verified;
        numbers print the .NET way (``3.0`` is ``3``), points and vectors as ``x,y,z``; a missing
        argument prints as empty text; a malformed format raises ``ValueError`` (Grasshopper emits
        null). ``culture`` is a .NET culture name (``de-DE`` swaps the separators); the invariant
        culture is the default.
    """

    display_name = "Format"
    nickname = "Format"
    gh_guid = "758d91a0-4aec-47f8-9671-16739a8a2c5d"

    inputs = [
        InputParam("format", str, Access.ITEM, default=""),
        InputParam("culture", str, Access.ITEM, default=""),
        InputParam("data", None, Access.ITEM, optional=True),
    ]
    outputs = [
        OutputParam("text", str),
    ]
    variadic_inputs = True

    def generate(self, format="", culture="", data=None):
        return format_composite(str(format), list(data or []), str(culture or ""))
