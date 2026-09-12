"""Golden-file helpers.

Golden JSON lives under ``tests/golden/``. Set ``PYHOPPER_UPDATE_GOLDEN=1``
to (re)write goldens from the current code instead of asserting against them.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

TESTS_DIR = Path(__file__).resolve().parents[1]
GOLDEN_DIR = TESTS_DIR / "golden"
UPDATE = os.environ.get("PYHOPPER_UPDATE_GOLDEN") == "1"


def golden_path(*parts: str) -> Path:
    return GOLDEN_DIR.joinpath(*parts)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=1, ensure_ascii=False, sort_keys=False)
        handle.write("\n")


def load_or_record(path: Path, produce) -> tuple[Any, bool]:
    """Return ``(golden, recorded)``; records when updating or when no golden exists yet."""
    if UPDATE or not path.exists():
        data = produce()
        save_json(path, data)
        return data, True
    return load_json(path), False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")
