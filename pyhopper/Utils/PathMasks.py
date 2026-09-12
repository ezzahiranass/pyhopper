"""Grasshopper's path rule notation and relative-offset masks.

A path mask is a ``{…}`` block of ``;``-separated rules, each one of: an
integer, ``?`` (exactly one index), ``*`` (any run of indices, possibly
none), ``(a,b,c)`` (one of), ``(a to b)`` (inclusive range), ``>n``, ``>=n``,
``<n``, ``<=n`` and ``!rule`` (negation). Everything else — text outside the
braces, negative integers, empty rules — is rejected the way Grasshopper
rejects it. Relative offsets look like ``{0;+1}[-1]``: a path offset block and
an optional item offset block.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Sequence

from pyhopper.Core.Path import Path

_INT = re.compile(r"^\d+$")
_BLOCKS = re.compile(r"\{([^{}]*)\}")


@dataclass(frozen=True)
class PathMask:
    rules: tuple[Callable[[int], bool] | str, ...]  # "?" / "*" markers or index predicates

    def matches(self, path: Path) -> bool:
        return _match(list(self.rules), list(path))


def _match(rules: list, indices: list[int]) -> bool:
    if not rules:
        return not indices
    head = rules[0]
    if head == "*":
        return any(_match(rules[1:], indices[skip:]) for skip in range(len(indices) + 1))
    if not indices:
        return False
    if head == "?" or head(indices[0]):
        return _match(rules[1:], indices[1:])
    return False


def _integer(token: str) -> int:
    token = token.strip()
    if token.startswith("-"):
        raise ValueError(f"Rule notation demands positive integers: {token}")
    if not _INT.match(token):
        raise ValueError(f"'{token}' is not a recognized rule notation symbol")
    return int(token)


def _parse_rule(text: str):
    rule = text.strip()
    if not rule:
        raise ValueError("Rule notation disallows empty rules")
    if rule == "*":
        return "*"
    if rule == "?":
        return "?"
    if rule.startswith("!"):
        inner = _parse_rule(rule[1:])
        if inner in ("*", "?"):
            raise ValueError("Rule notation cannot negate wildcards")
        return lambda index, inner=inner: not inner(index)
    for symbol, test in ((">=", lambda a, b: a >= b), ("<=", lambda a, b: a <= b), (">", lambda a, b: a > b), ("<", lambda a, b: a < b)):
        if rule.startswith(symbol):
            bound = _integer(rule[len(symbol):])
            return lambda index, bound=bound, test=test: test(index, bound)
    if rule.startswith("(") and rule.endswith(")"):
        body = rule[1:-1].strip()
        if " to " in body:
            low, high = (_integer(part) for part in body.split(" to ", 1))
            return lambda index, low=low, high=high: low <= index <= high
        allowed = {_integer(part) for part in body.split(",")}
        return lambda index, allowed=allowed: index in allowed
    if rule.startswith("(") or rule.endswith(")"):
        raise ValueError(f"Rule '{rule}' has unbalanced parentheses")
    value = _integer(rule)
    return lambda index, value=value: index == value


def parse_path_mask(mask: str) -> PathMask:
    """Parse ``{rule;rule;…}`` into a matcher; raises ``ValueError`` for invalid notation."""
    text = str(mask)
    stripped = re.sub(r"\[[^\[\]]*\]", "", text)  # item blocks are ignored by path comparisons
    blocks = _BLOCKS.findall(stripped)
    outside = _BLOCKS.sub("", stripped).strip()
    if outside or not blocks:
        raise ValueError("Rule notation disallows the use of any symbol outside of '{ }' or '[ ]' blocks")
    if len(blocks) != 1:
        raise ValueError("Rule notation allows a single '{ }' block")
    return PathMask(tuple(_parse_rule(part) for part in blocks[0].split(";")))


def path_matches(path: Path, mask: str) -> bool:
    return parse_path_mask(mask).matches(path)


@dataclass(frozen=True)
class RelativeOffset:
    path: tuple[int, ...]
    item: int


_OFFSET = re.compile(r"^\s*\{([^{}]*)\}\s*(?:\[\s*([+-]?\d+)\s*\])?\s*$")


def parse_relative_offset(mask: str) -> RelativeOffset:
    """Parse ``{0;+1}[-1]``: signed (or unsigned) path offsets and an optional item offset."""
    match = _OFFSET.match(str(mask))
    if not match or not match.group(1).strip():
        raise ValueError("Offset mask is not valid")
    try:
        offsets = tuple(int(part.strip()) for part in match.group(1).split(";"))
    except ValueError:
        raise ValueError("Offset mask is not valid") from None
    return RelativeOffset(offsets, int(match.group(2)) if match.group(2) is not None else 0)


def offset_path(path: Path, offsets: Sequence[int], all_paths: Sequence[Path], wrap: bool) -> Path | None:
    """The path ``offsets`` away from ``path``; with ``wrap`` every offset dimension wraps within the
    indices that exist among the paths sharing its prefix (Grasshopper-verified). ``None`` when the
    target does not exist."""
    indices = list(path)
    for dimension, offset in enumerate(offsets):
        if dimension >= len(indices):
            break
        if not offset:
            continue
        target = indices[dimension] + offset
        if wrap:
            prefix = tuple(indices[:dimension])
            siblings = sorted({p[dimension] for p in all_paths if len(p) > dimension and tuple(p[:dimension]) == prefix})
            if indices[dimension] in siblings and siblings:
                position = (siblings.index(indices[dimension]) + offset) % len(siblings)
                target = siblings[position]
        indices[dimension] = target
    result = Path(*indices)
    return result if result in set(all_paths) else None
