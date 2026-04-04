from __future__ import annotations

from dataclasses import dataclass, field
from threading import Event, Lock


@dataclass
class RunCancellation:
    run_id: str
    conversation_id: str
    request_id: str
    stop_event: Event = field(default_factory=Event)


_registry_lock = Lock()
_registry: dict[str, RunCancellation] = {}


def register_run(*, run_id: str, conversation_id: str, request_id: str) -> RunCancellation:
    record = RunCancellation(
        run_id=str(run_id or "").strip(),
        conversation_id=str(conversation_id or "").strip(),
        request_id=str(request_id or "").strip(),
    )
    with _registry_lock:
        _registry[record.run_id] = record
    return record


def unregister_run(run_id: str) -> None:
    normalized = str(run_id or "").strip()
    if not normalized:
        return
    with _registry_lock:
        _registry.pop(normalized, None)


def get_run(run_id: str) -> RunCancellation | None:
    normalized = str(run_id or "").strip()
    if not normalized:
        return None
    with _registry_lock:
        return _registry.get(normalized)


def request_stop(run_id: str, *, conversation_id: str = "") -> bool:
    record = get_run(run_id)
    if record is None:
        return False
    if conversation_id and record.conversation_id != str(conversation_id).strip():
        return False
    record.stop_event.set()
    return True


def is_stop_requested(run_id: str) -> bool:
    record = get_run(run_id)
    return bool(record and record.stop_event.is_set())
