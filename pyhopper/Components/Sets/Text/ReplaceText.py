"""ReplaceText - Replace text fragments."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class ReplaceText(Component):
    """Replace all occurrences of a text fragment with another fragment."""

    inputs = [
        InputParam("text", str, Access.ITEM),
        InputParam("find", str, Access.ITEM),
        InputParam("replace", str, Access.ITEM, default=""),
    ]
    outputs = [OutputParam("result", str)]

    def generate(self, text="", find="", replace=""):
        if not find:
            raise ValueError("ReplaceText find fragment cannot be empty")
        return text.replace(find, replace)
