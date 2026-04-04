from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Iterator


StreamEmitter = Callable[[dict[str, Any]], None]

_stream_emitter: ContextVar[StreamEmitter | None] = ContextVar("agent_stream_emitter", default=None)


@contextmanager
def use_stream_emitter(emitter: StreamEmitter) -> Iterator[None]:
    token = _stream_emitter.set(emitter)
    try:
        yield
    finally:
        _stream_emitter.reset(token)


def emit_stream_event(event_type: str, data: dict[str, Any]) -> None:
    emitter = _stream_emitter.get()
    if emitter is None:
        return
    emitter({"type": event_type, "data": data})


def format_sse_event(event: dict[str, Any]) -> str:
    payload = json.dumps(event.get("data") or {}, ensure_ascii=True, default=str)
    return f"event: {event.get('type') or 'message'}\ndata: {payload}\n\n"

