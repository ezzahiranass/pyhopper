"""Characters - Break text into characters and Unicode values."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Characters(Component):
    """Break text into character and Unicode-code-point lists."""

    inputs = [InputParam("text", str, Access.ITEM)]
    outputs = [
        OutputParam("result", str),
        OutputParam("unicode", int),
    ]

    def generate(self, text=""):
        characters = list(text)
        return characters, [ord(character) for character in characters]
