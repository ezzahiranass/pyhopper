from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict


NEW_AGENTS_DIR = Path(__file__).resolve().parent


class JobOverview(TypedDict):
    slug: str
    title: str
    description: str
    tools: list[str]


def _load_overviews_from(root: Path) -> list[JobOverview]:
    overviews: list[JobOverview] = []

    for job_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        overview_path = job_dir / "overview.json"
        if not overview_path.exists():
            continue

        data = json.loads(overview_path.read_text(encoding="utf-8"))
        overviews.append(
            {
                "slug": str(data.get("slug") or job_dir.name),
                "title": str(data.get("title") or job_dir.name.replace("_", " ").title()),
                "description": str(data.get("description") or "").strip(),
                "tools": [str(tool) for tool in data.get("tools") or [] if str(tool).strip()],
            }
        )

    return overviews


@lru_cache(maxsize=1)
def load_job_overviews() -> list[JobOverview]:
    return sorted(_load_overviews_from(NEW_AGENTS_DIR), key=lambda item: item["title"].lower())


def get_valid_job_titles() -> set[str]:
    return {overview["title"] for overview in load_job_overviews()}
