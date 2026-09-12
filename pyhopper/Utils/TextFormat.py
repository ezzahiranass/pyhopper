""".NET composite formatting for the Grasshopper ``Format`` component.

Supports the subset Grasshopper users actually type: ``{0}``, ``{1,10}`` /
``{1,-10}`` alignment, the standard numeric formats ``D E F G N P X R``
(``{0:F2}``, ``{0:N0}``, ``{0:P1}``, ``{0:X}``), custom numeric pictures
(``{0:0.00}``, ``{0:#,##0.###}``, ``{0:0%}``, ``{0:0.0E+00}``,
``{0:0.0;(0.0);zero}``) and ``{{`` / ``}}`` escapes, with the number
separators of a few common cultures (invariant by default). Missing arguments
print as empty text like Grasshopper; malformed formats raise ``ValueError``.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Sequence

from pyhopper.Utils.Text import format_number

_PLACEHOLDER = re.compile(r"\{(\d+)(?:,(-?\d+))?(?::([^{}]*))?\}")


@dataclass(frozen=True)
class Culture:
    decimal: str = "."
    group: str = ","
    percent_pattern: str = "n %"  # .NET PercentPositivePattern 0; en-US uses "n%"


_CULTURES = {
    "": Culture(),
    "invariant": Culture(),
    "en-us": Culture(percent_pattern="n%"),
    "en-gb": Culture(percent_pattern="n%"),
    "en": Culture(percent_pattern="n%"),
    "de-de": Culture(decimal=",", group="."),
    "de": Culture(decimal=",", group="."),
    "nl-nl": Culture(decimal=",", group="."),
    "es-es": Culture(decimal=",", group="."),
    "it-it": Culture(decimal=",", group="."),
    "pt-br": Culture(decimal=",", group="."),
    "fr-fr": Culture(decimal=",", group=" "),
    "fr": Culture(decimal=",", group=" "),
    "ru-ru": Culture(decimal=",", group=" "),
}


def culture_for(name: str | None) -> Culture:
    """Number separators for a culture name (``de-DE``, ``en-US`` …); unknown names are invariant."""
    return _CULTURES.get((name or "").strip().lower(), Culture())


def value_text(value: Any) -> str:
    """Grasshopper's plain text for an item: numbers the .NET way, points and vectors as ``x,y,z``."""
    if isinstance(value, str):
        return value
    if isinstance(value, (bool, int, float)):
        return format_number(value)
    if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
        return ",".join(format_number(float(getattr(value, axis))) for axis in "xyz")
    return str(value)


def format_composite(template: str, arguments: Sequence[Any], culture: str | None = None) -> str:
    """Expand a .NET composite format string with ``arguments`` (missing ones print as empty text)."""
    settings = culture_for(culture)
    text = template.replace("{{", "\x00").replace("}}", "\x01")
    if re.search(r"\{(?![0-9])|\{\d+[^}]*$", text) or re.search(r"(?<!\d)}|^}", re.sub(_PLACEHOLDER, "", text)):
        raise ValueError("Format string is not in the correct format")

    def expand(match: re.Match) -> str:
        index, alignment, spec = int(match.group(1)), match.group(2), match.group(3)
        value = arguments[index] if index < len(arguments) else None
        rendered = "" if value is None else format_item(value, spec, settings)
        if alignment:
            width = int(alignment)
            rendered = rendered.rjust(width) if width > 0 else rendered.ljust(-width)
        return rendered

    return _PLACEHOLDER.sub(expand, text).replace("\x00", "{").replace("\x01", "}")


def format_item(value: Any, spec: str | None, settings: Culture) -> str:
    """One argument with an optional format specifier."""
    is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
    if not spec:
        return value_text(value)
    if not is_number:
        return value_text(value)
    return format_numeric(value, spec, settings)


# ── numbers ────────────────────────────────────────────────────────

def _group(integer: str, settings: Culture) -> str:
    parts = []
    while len(integer) > 3:
        parts.insert(0, integer[-3:])
        integer = integer[:-3]
    parts.insert(0, integer)
    return settings.group.join(parts)


def _fixed(value: float, decimals: int, settings: Culture, grouping: bool = False) -> str:
    text = f"{abs(value):.{decimals}f}"
    integer, _, fraction = text.partition(".")
    if grouping:
        integer = _group(integer, settings)
    body = integer + (settings.decimal + fraction if fraction else "")
    negative = value < 0 and any(ch not in "0" for ch in text if ch.isdigit())
    return ("-" if negative else "") + body


def _scientific(value: float, decimals: int, marker: str, settings: Culture) -> str:
    text = f"{value:.{decimals}E}"
    mantissa, exponent = text.split("E")
    sign = exponent[0]
    digits = exponent[1:].rjust(3, "0")
    return mantissa.replace(".", settings.decimal) + marker + sign + digits


def format_numeric(value: float | int, spec: str, settings: Culture) -> str:
    """Standard (``F2``, ``N``, ``P1``, ``E``, ``G``, ``D4``, ``X``, ``R``) or custom (``0.00``) numeric format."""
    standard = re.fullmatch(r"([A-Za-z])(\d*)", spec)
    if standard:
        letter, precision = standard.group(1), standard.group(2)
        digits = int(precision) if precision else None
        upper = letter.upper()
        if upper == "F":
            return _fixed(float(value), 2 if digits is None else digits, settings)
        if upper == "N":
            return _fixed(float(value), 2 if digits is None else digits, settings, grouping=True)
        if upper == "P":
            number = _fixed(float(value) * 100.0, 2 if digits is None else digits, settings, grouping=True)
            return settings.percent_pattern.replace("n", number)
        if upper == "E":
            return _scientific(float(value), 6 if digits is None else digits, letter, settings)
        if upper == "D":
            if isinstance(value, float):
                raise ValueError("Format 'D' needs an integer")
            body = str(abs(value)).rjust(digits or 0, "0")
            return ("-" if value < 0 else "") + body
        if upper == "X":
            if isinstance(value, float):
                raise ValueError("Format 'X' needs an integer")
            body = format(abs(value), "X" if letter == "X" else "x").rjust(digits or 0, "0")
            return ("-" if value < 0 else "") + body
        if upper in ("G", "R"):
            if digits and upper == "G":
                text = f"{float(value):.{digits}g}"
                if "e" in text:
                    mantissa, exponent = text.split("e")
                    text = f"{mantissa}E{exponent[0]}{exponent[1:].rjust(2, '0')}"
                return text.replace(".", settings.decimal)
            return format_number(value).replace(".", settings.decimal)
        if upper == "C":
            return "¤" + _fixed(float(value), 2 if digits is None else digits, settings, grouping=True)
        raise ValueError(f"Unknown numeric format '{spec}'")
    return format_custom(float(value), spec, settings)


def _split_sections(spec: str) -> list[str]:
    sections, current, quote = [], [], None
    for ch in spec:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            current.append(ch)
        elif ch == ";":
            sections.append("".join(current))
            current = []
        else:
            current.append(ch)
    sections.append("".join(current))
    return sections


def format_custom(value: float, spec: str, settings: Culture) -> str:
    """A .NET custom numeric picture (``0``, ``#``, ``.``, ``,``, ``%``, ``‰``, ``E+0`` and literals)."""
    sections = _split_sections(spec)
    picture, show_sign = sections[0], True
    if value < 0 and len(sections) >= 2 and sections[1] != "":
        picture, value, show_sign = sections[1], -value, False
    elif value == 0 and len(sections) >= 3 and sections[2] != "":
        picture = sections[2]

    tokens = _tokenize(picture)
    if not any(kind == "digits" for kind, _ in tokens):
        # no digit placeholders: only the literals print (Grasshopper renders "{0:%}" as "%")
        return "".join(text for kind, text in tokens if kind != "E")

    scale = 1.0
    for kind, _ in tokens:
        scale *= {"%": 100.0, "‰": 1000.0}.get(kind, 1.0)
    number = value * scale
    digits = "".join(text for kind, text in tokens if kind == "digits")
    before, _, after = digits.partition(".")
    grouping = "," in before
    before = before.replace(",", "")
    min_integer = len(before) - before.index("0") if "0" in before else 0
    decimals = len(after)
    required_decimals = len(after.rstrip("#"))

    exponent = 0
    exponent_token = next((text for kind, text in tokens if kind == "E"), None)
    if exponent_token and number != 0.0:
        exponent = int(math.floor(math.log10(abs(number)))) - (max(len(before), 1) - 1)
        number = number / 10.0 ** exponent

    fixed = f"{abs(number):.{decimals}f}"
    integer, _, fraction = fixed.partition(".")
    integer = integer.lstrip("0").rjust(min_integer, "0")
    if grouping and integer:
        integer = _group(integer, settings)
    if len(fraction) > required_decimals:
        fraction = fraction[:required_decimals] + fraction[required_decimals:].rstrip("0")
    number_text = integer + (settings.decimal + fraction if fraction else "")
    negative = show_sign and number < 0 and any(ch != "0" for ch in fixed if ch.isdigit())

    out, printed = [], False
    for kind, text in tokens:
        if kind == "digits":
            if not printed:
                out.append(number_text)
                printed = True
        elif kind == "E":
            sign = "-" if exponent < 0 else ("+" if text[1] == "+" else "")
            out.append(text[0] + sign + str(abs(exponent)).rjust(len(text) - 2, "0"))
        else:
            out.append(text)
    return ("-" if negative else "") + "".join(out)


def _tokenize(picture: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    i = 0
    run = []

    def flush():
        if run:
            tokens.append(("digits", "".join(run)))
            run.clear()

    while i < len(picture):
        ch = picture[i]
        if ch in "0#.,":
            run.append(ch)
            i += 1
        elif ch in "Ee" and i + 1 < len(picture) and (picture[i + 1] in "+-0"):
            flush()
            j = i + 1
            sign = picture[j] if picture[j] in "+-" else ""
            j += 1 if sign else 0
            zeros = 0
            while j < len(picture) and picture[j] == "0":
                zeros += 1
                j += 1
            tokens.append(("E", ch + (sign or "-") + "0" * zeros))
            i = j
        elif ch == "%":
            flush()
            tokens.append(("%", "%"))
            i += 1
        elif ch == "‰":
            flush()
            tokens.append(("‰", "‰"))
            i += 1
        elif ch in "'\"":
            flush()
            end = picture.find(ch, i + 1)
            end = len(picture) if end < 0 else end
            tokens.append(("literal", picture[i + 1:end]))
            i = end + 1
        elif ch == "\\" and i + 1 < len(picture):
            flush()
            tokens.append(("literal", picture[i + 1]))
            i += 2
        else:
            flush()
            tokens.append(("literal", ch))
            i += 1
    flush()
    return tokens
