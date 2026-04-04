from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Iterator
from uuid import uuid4

from colorama import Fore, Style, init

from .streaming import emit_stream_event

init(autoreset=True)

TRACE_ENABLED = True
_MAX_PREVIEW = 10


_trace_stack: ContextVar[tuple[str, ...]] = ContextVar("agent_trace_stack", default=())


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _request_prefix(request_id: str | None) -> str:
    return f"[{_now()}][req:{request_id or '-'}]"


def _preview(value: Any, max_len: int = _MAX_PREVIEW) -> str:
    if isinstance(value, str):
        text = " ".join(value.split())
    else:
        try:
            import json

            text = json.dumps(value, ensure_ascii=True, default=str)
        except TypeError:
            text = str(value)

    if len(text) <= max_len:
        return text
    return f"{text[:max_len - 3]}..."


def _emit(color: str, request_id: str | None, label: str, message: str) -> None:
    if not TRACE_ENABLED:
        return
    print(f"{Style.DIM}{_request_prefix(request_id)}{Style.RESET_ALL} {color}{label:<10}{Style.RESET_ALL} {message}")


def backend_event(request_id: str | None, message: str) -> None:
    _emit(Fore.CYAN, request_id, "BACKEND", message)


def dispatch_event(request_id: str | None, message: str) -> None:
    _emit(Fore.MAGENTA, request_id, "DISPATCH", message)


def graph_event(request_id: str | None, message: str) -> None:
    _emit(Fore.BLUE, request_id, "GRAPH", message)


def agent_event(request_id: str | None, message: str) -> None:
    _emit(Fore.GREEN, request_id, "AGENT", message)


def tool_event(request_id: str | None, message: str) -> None:
    _emit(Fore.YELLOW, request_id, "TOOL", message)


def error_event(request_id: str | None, message: str) -> None:
    _emit(Fore.RED, request_id, "ERROR", message)


def log_http_request(request_id: str, payload: dict, messages: list[dict]) -> None:
    backend_event(
        request_id,
        (
            "POST /chat/respond/stream "
            f"job={payload.get('responderJob') or '-'} "
            f"team={payload.get('teamId') or '-'} "
            f"messages={len(messages)}"
        ),
    )
    if messages:
        last_message = messages[-1]
        backend_event(
            request_id,
            (
                "latest message "
                f"role={last_message.get('role') or '-'} "
                f"author={last_message.get('author') or '-'} "
                f"content=\"{_preview(last_message.get('content') or '')}\""
            ),
        )


def log_final_response(request_id: str | None, response: str) -> None:
    agent_event(request_id, f"final response=\"{_preview(response)}\"")


def _normalize_node(node: str) -> str:
    return str(node or "").strip().lower().replace(" ", "_").replace("-", "_")


def current_trace_node() -> str:
    stack = _trace_stack.get()
    return "/".join(stack)


@contextmanager
def trace_scope(node: str) -> Iterator[str]:
    normalized = _normalize_node(node)
    stack = _trace_stack.get()
    next_stack = (*stack, normalized) if normalized else stack
    token = _trace_stack.set(next_stack)
    try:
        current = current_trace_node()
        if current:
            emit_stream_event("node.entered", {"node": current})
        yield current
    finally:
        _trace_stack.reset(token)


def emit_commentary_delta(text: str, *, node: str | None = None) -> None:
    content = str(text or "")
    if not content:
        return
    emit_stream_event(
        "commentary.delta",
        {
            "node": node or current_trace_node(),
            "textDelta": content,
        },
    )


def emit_commentary_completed(text: str, *, node: str | None = None, status_text: str | None = None) -> None:
    content = str(text or "").strip()
    if not content:
        return

    data = {
        "node": node or current_trace_node(),
        "text": content,
    }
    if status_text:
        data["statusText"] = str(status_text)

    emit_stream_event("commentary.completed", data)


def emit_tool_started(tool_name: str, *, args=None, node: str | None = None, call_id: str | None = None) -> str:
    resolved_call_id = str(call_id or uuid4().hex[:8])
    emit_stream_event(
        "tool.started",
        {
            "node": node or current_trace_node(),
            "toolName": str(tool_name or ""),
            "callId": resolved_call_id,
            "args": args,
        },
    )
    return resolved_call_id


def emit_tool_completed(tool_name: str, call_id: str, *, output=None, node: str | None = None) -> None:
    emit_stream_event(
        "tool.completed",
        {
            "node": node or current_trace_node(),
            "toolName": str(tool_name or ""),
            "callId": str(call_id),
            "output": output,
        },
    )


def emit_tool_failed(tool_name: str, call_id: str, error: str, *, node: str | None = None) -> None:
    emit_stream_event(
        "tool.failed",
        {
            "node": node or current_trace_node(),
            "toolName": str(tool_name or ""),
            "callId": str(call_id),
            "error": str(error or "Tool execution failed."),
        },
    )
