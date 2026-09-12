"""CharSequence - Create a sequence of textual characters (Grasshopper "Char Sequence")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class CharSequence(Component):
    """Create a sequence of textual characters.

    Inputs:
        count: Number of elements in the sequence. (Grasshopper Count [item]).
        char_pool: Pool of characters available to the sequence. (Grasshopper Char Pool [item]).
        format: Optional formatting mask (Grasshopper Format [item]).

    Outputs:
        sequence: Sequence of character tags (Grasshopper Sequence).

    Notes:
        Grasshopper: Sets > Sequence > Char Sequence (CharSeq).
        pyhopper decisions: bijective numeration over the pool (``A … Z, AA, AB, …``, verified for
        the pool "AB"); ``format`` substitutes ``{0}`` with each code (a .NET composite format;
        only the ``{0}`` placeholder is supported); an empty pool or a zero count gives an empty
        list. Defaults 10, A–Z and ``{0}`` as in Grasshopper.
    """

    display_name = "Char Sequence"
    nickname = "CharSeq"
    gh_guid = "01640871-69ea-40ac-9380-4660d6d28bd2"

    inputs = [
        InputParam("count", int, Access.ITEM, default=10),
        InputParam("char_pool", str, Access.ITEM, default="ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        InputParam("format", str, Access.ITEM, default="{0}"),
    ]
    outputs = [
        OutputParam("sequence", str, access=Access.LIST),
    ]

    def generate(self, count=10, char_pool="ABCDEFGHIJKLMNOPQRSTUVWXYZ", format="{0}"):
        pool = str(char_pool)
        total = int(count)
        if not pool or total <= 0:
            return []
        template = "{0}" if format is None else str(format)
        codes = []
        for number in range(1, total + 1):
            digits = []
            while number > 0:
                number, remainder = divmod(number - 1, len(pool))
                digits.append(pool[remainder])
            codes.append(template.replace("{0}", "".join(reversed(digits))))
        return codes
