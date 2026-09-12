"""MatchText - Match a text against a pattern (Grasshopper "Match Text")."""

from __future__ import annotations

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
import re

from pyhopper.Utils.Text import wildcard_to_regex


class MatchText(Component):
    """Match a text against a pattern.

    Inputs:
        text: Text to match (Grasshopper Text [item]).
        pattern: Optional wildcard pattern for matching (Grasshopper Pattern [item]).
        regex: Optional RegEx pattern for matching (Grasshopper RegEx [item]).
        case: Compare using case-sensitive matching (Grasshopper Case [item]).

    Outputs:
        matched: True if the text adheres to all supplied patterns (Grasshopper Match).

    Notes:
        Grasshopper: Sets > Text > Match Text (TMatch).
        pyhopper decisions: ``pattern`` is a Grasshopper wildcard (``*`` any run, ``?`` one
        character, ``#`` one digit, ``[abc]`` one of a set), ``regex`` a regular expression; when
        both are given both must match, with neither everything matches; ``case`` (default True)
        makes both comparisons case-sensitive. Grasshopper-verified.
    """

    display_name = "Match Text"
    nickname = "TMatch"
    gh_guid = "3756c55f-95c3-442c-a027-6b3ab0455a94"

    inputs = [
        InputParam("text", str, Access.ITEM, default=""),
        InputParam("pattern", str, Access.ITEM, optional=True),
        InputParam("regex", str, Access.ITEM, optional=True),
        InputParam("case", bool, Access.ITEM, default=True),
    ]
    outputs = [
        OutputParam("matched", bool),
    ]

    def generate(self, text="", pattern=None, regex=None, case=True):
        flags = 0 if case else re.IGNORECASE
        subject = str(text)
        if pattern is not None and not re.fullmatch(wildcard_to_regex(str(pattern)), subject, flags):
            return False
        if regex is not None and not re.search(str(regex), subject, flags):
            return False
        return True
