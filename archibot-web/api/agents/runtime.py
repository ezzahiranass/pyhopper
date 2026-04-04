from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator


_runtime_context: ContextVar[dict[str, Any]] = ContextVar("agent_runtime_context", default={})


@contextmanager
def use_runtime_context(values: dict[str, Any]) -> Iterator[None]:
    token = _runtime_context.set(dict(values or {}))
    try:
        yield
    finally:
        _runtime_context.reset(token)


def get_runtime_context() -> dict[str, Any]:
    return dict(_runtime_context.get() or {})


def resolve_runtime_identity(
    *,
    default_name: str = "Agent",
    default_job: str = "Agent",
    default_description: str = "An architecture studio agent.",
    default_personality: str = "",
) -> dict[str, str]:
    runtime = get_runtime_context()
    return {
        "name": str(runtime.get("responder_name") or default_name).strip() or default_name,
        "job": str(runtime.get("responder_job") or default_job).strip() or default_job,
        "description": str(runtime.get("responder_description") or default_description).strip() or default_description,
        "personality": str(runtime.get("responder_personality") or default_personality).strip(),
    }


def resolve_runtime_conversation_context() -> dict[str, Any]:
    runtime = get_runtime_context()
    return {
        "conversation_kind": str(runtime.get("conversation_kind") or "channel").strip() or "channel",
        "conversation_title": str(runtime.get("conversation_title") or "").strip(),
        "conversation_participants": list(runtime.get("conversation_participants") or []),
        "available_agents": list(runtime.get("available_agents") or []),
    }
