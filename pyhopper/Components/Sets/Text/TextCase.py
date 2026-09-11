"""TextCase - Convert text to upper- and lower-case forms."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


def _turkish_upper(text: str) -> str:
    return text.replace("i", "\u0130").replace("\u0131", "I").upper()


def _turkish_lower(text: str) -> str:
    return text.replace("I", "\u0131").replace("\u0130", "i").lower()


class TextCase(Component):
    """Change the casing of text using optional culture-name rules.

    Culture is represented as a culture-name string. Turkish and Azeri names
    receive their language-specific dotted and dotless-I casing behavior.
    """

    inputs = [
        InputParam("text", str, Access.ITEM),
        InputParam("culture", str, Access.ITEM, default=""),
    ]
    outputs = [
        OutputParam("upper_case", str),
        OutputParam("lower_case", str),
    ]

    def generate(self, text="", culture=""):
        language = culture.replace("_", "-").split("-", 1)[0].lower()
        if language in {"tr", "az"}:
            return _turkish_upper(text), _turkish_lower(text)
        return text.upper(), text.lower()
