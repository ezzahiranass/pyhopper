"""TextSplit - Split text using separator characters."""

import re

from pyhopper.Core.Component import Access, Component, InputParam, OutputParam


class TextSplit(Component):
    """Split text into fragments using each supplied separator character."""

    inputs = [
        InputParam("text", str, Access.ITEM),
        InputParam("separators", str, Access.ITEM),
    ]
    outputs = [OutputParam("result", str, access=Access.LIST)]

    def generate(self, text="", separators=""):
        if not separators:
            return [text]
        return re.split(f"[{re.escape(separators)}]", text)
