from __future__ import annotations

import time
from typing import Any

from .client import get_firestore_client


def _run_ref(conversation_id: str, run_id: str):
    db = get_firestore_client()
    return db.collection("conversations").document(conversation_id).collection("agentRuns").document(run_id)


def save_agent_run(conversation_id: str, run_id: str, payload: dict[str, Any]) -> None:
    if not conversation_id or not run_id:
        return

    now = int(time.time() * 1000)
    run_ref = _run_ref(conversation_id, run_id)
    existing = run_ref.get()
    next_payload = {
        **payload,
        "conversationId": conversation_id,
        "runId": run_id,
        "updatedAt": now,
    }
    if not existing.exists:
        next_payload.setdefault("createdAt", now)

    run_ref.set(next_payload, merge=True)


def load_agent_run(conversation_id: str, run_id: str) -> dict[str, Any] | None:
    if not conversation_id or not run_id:
        return None

    run_doc = _run_ref(conversation_id, run_id).get()
    if not run_doc.exists:
        return None
    return run_doc.to_dict() or {}
