"""Characters - Break text into characters and Unicode values."""

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class Characters(Component):
    """Break text into character and Unicode-code-point lists."""

    inputs = [InputParam("text", str, Access.ITEM)]
    outputs = [
        OutputParam("result", str, access=Access.LIST),
        OutputParam("unicode", int, access=Access.LIST),
    ]

    def generate(self, text=""):
        characters = list(text)
        return characters, [ord(character) for character in characters]
