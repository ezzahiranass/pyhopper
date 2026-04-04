from __future__ import annotations

import re
import traceback
from queue import Empty, Queue
from threading import Thread
from time import perf_counter
from typing import Callable, Iterable, Sequence
from uuid import uuid4

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

_IMPORT_STARTED_AT = perf_counter()


def _boot_log(stage: str) -> None:
    elapsed = perf_counter() - _IMPORT_STARTED_AT
    print(f"[BOOT agents.main +{elapsed:7.3f}s] {stage}", flush=True)


_boot_log("starting module import")

from langchain_core.messages import AIMessage, HumanMessage

_boot_log("imported langchain_core.messages")

from .cancellation import is_stop_requested, register_run, unregister_run
from .streaming import use_stream_emitter
from .trace import dispatch_event, error_event, log_final_response

_boot_log("imported core helpers")

from .administrative_assistant.agent import ask_stream as ask_administrative_assistant_stream
_boot_log("imported administrative_assistant.agent")
from .accountant.agent import ask_stream as ask_accountant_stream
_boot_log("imported accountant.agent")
from .archviz_artist.agent import ask_stream as ask_archviz_artist_stream
_boot_log("imported archviz_artist.agent")
from .cad_drafter.agent import ask_stream as ask_cad_drafter_stream
_boot_log("imported cad_drafter.agent")
from .computational_designer.agent import ask_stream as ask_computational_designer_stream
_boot_log("imported computational_designer.agent")
from .core.agent import ask_stream as ask_main_stream
_boot_log("imported core.agent")
from .intern.agent import ask_stream as ask_intern_stream
_boot_log("imported intern.agent")
from .junior_architect.agent import ask_stream as ask_junior_stream
_boot_log("imported junior_architect.agent")
from .manager.agent import ask_stream as ask_manager_stream
_boot_log("imported manager.agent")
from .senior_architect.agent import ask_stream as ask_senior_architect_stream
_boot_log("imported senior_architect.agent")
from .runtime import use_runtime_context

_boot_log("imported runtime")

if load_dotenv is not None:
    load_dotenv()
    _boot_log("loaded environment variables")


AgentStream = Callable[[str, Sequence | None], Iterable[str]]

_AGENT_STREAMS: dict[str, AgentStream] = {
    "architect": ask_main_stream,
    "accountant": ask_accountant_stream,
    "administrative_assistant": ask_administrative_assistant_stream,
    "assistant": ask_administrative_assistant_stream,
    "archviz_artist": ask_archviz_artist_stream,
    "cad_drafter": ask_cad_drafter_stream,
    "computational_designer": ask_computational_designer_stream,
    "intern": ask_intern_stream,
    "junior": ask_junior_stream,
    "junior_architect": ask_junior_stream,
    "manager": ask_manager_stream,
    "senior_architect": ask_senior_architect_stream,
}


def _normalize_agent_key(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _resolve_agent_stream(payload: dict) -> tuple[str, AgentStream]:
    raw_candidates = [
        payload.get("responderJob"),
        payload.get("responderName"),
        payload.get("currentResponderRef"),
    ]

    for candidate in raw_candidates:
        normalized = _normalize_agent_key(str(candidate or "").split(":")[-1])
        if normalized in _AGENT_STREAMS:
            return normalized, _AGENT_STREAMS[normalized]

    responder_job = str(payload.get("responderJob") or "")
    normalized_job = _normalize_agent_key(responder_job)

    if "intern" in normalized_job:
        return "intern", ask_intern_stream
    if "account" in normalized_job:
        return "accountant", ask_accountant_stream
    if "administrative" in normalized_job and "assistant" in normalized_job:
        return "administrative_assistant", ask_administrative_assistant_stream
    if "archviz" in normalized_job or ("visual" in normalized_job and "artist" in normalized_job):
        return "archviz_artist", ask_archviz_artist_stream
    if "cad" in normalized_job and "draft" in normalized_job:
        return "cad_drafter", ask_cad_drafter_stream
    if "computational" in normalized_job and "designer" in normalized_job:
        return "computational_designer", ask_computational_designer_stream
    if "junior" in normalized_job and "architect" in normalized_job:
        return "junior_architect", ask_junior_stream
    if "manager" in normalized_job:
        return "manager", ask_manager_stream
    if "senior" in normalized_job and "architect" in normalized_job:
        return "senior_architect", ask_senior_architect_stream

    raise LookupError(f"unsupported responder job '{responder_job or 'unknown'}'")


def _normalize_messages(messages: list[dict]) -> list[dict[str, str]]:
    normalized_messages: list[dict[str, str]] = []

    for item in messages:
        if not isinstance(item, dict):
            continue

        content = str(item.get("content") or "").strip()
        if not content:
            continue

        normalized_messages.append(
            {
                "role": "assistant" if item.get("role") == "assistant" else "user",
                "author_id": str(item.get("authorId") or "").strip(),
                "author": str(item.get("author") or "Unknown").strip() or "Unknown",
                "author_job": str(item.get("authorJob") or "").strip(),
                "author_kind": str(item.get("authorKind") or "").strip(),
                "content": content,
            }
        )

    return normalized_messages


def _speaker_label(message: dict[str, str]) -> str:
    author = str(message.get("author") or "Unknown").strip() or "Unknown"
    author_job = str(message.get("author_job") or "").strip()
    author_kind = str(message.get("author_kind") or "").strip()

    if author_job:
        return f"{author} ({author_job})"
    if author_kind == "agent":
        return f"{author} (Agent)"
    if author_kind == "user":
        return f"{author} (User)"
    return author


def _message_content_for_model(message: dict[str, str]) -> str:
    content = str(message.get("content") or "").strip()
    if message.get("role") == "assistant":
        return content
    return f"{_speaker_label(message)}: {content}"


def _strip_leading_self_identity(content: str, *, responder_name: str, responder_job: str) -> str:
    text = str(content or "").strip()
    if not text:
        return ""

    clean_name = str(responder_name or "").strip()
    clean_job = str(responder_job or "").strip()
    patterns: list[str] = []

    if clean_name and clean_job:
        patterns.append(rf"^{re.escape(clean_name)}\s*\(\s*{re.escape(clean_job)}\s*\)\s*:\s*")
    if clean_name:
        patterns.append(rf"^{re.escape(clean_name)}\s*:\s*")

    stripped = text
    for pattern in patterns:
        stripped = re.sub(pattern, "", stripped, count=1, flags=re.IGNORECASE).strip()

    return stripped or text


def _build_agent_inputs(messages: list[dict]) -> tuple[str, list[HumanMessage | AIMessage]]:
    normalized_messages = _normalize_messages(messages)
    if not normalized_messages:
        return "", []

    current_input = _message_content_for_model(normalized_messages[-1])
    history: list[HumanMessage | AIMessage] = []

    for item in normalized_messages[:-1]:
        if item["role"] == "assistant":
            history.append(AIMessage(content=_message_content_for_model(item)))
        else:
            history.append(HumanMessage(content=_message_content_for_model(item)))

    return current_input, history


def respond_stream(messages: list[dict], payload: dict):
    request_id = str(payload.get("requestId") or uuid4().hex[:8])
    run_id = str(payload.get("resumeRunId") or request_id)
    conversation_id = str(payload.get("conversationId") or "")
    user_input, history = _build_agent_inputs(messages)

    try:
        agent_key, stream_handler = _resolve_agent_stream(payload)
        dispatch_event(request_id, f"routing request to agents.{agent_key}")
    except LookupError as error:
        error_event(request_id, str(error))

        def failed_stream():
            yield {
                "type": "run.failed",
                "data": {
                    "error": str(error),
                    "content": (
                        f"I can't respond yet because the '{payload.get('responderJob') or 'unknown'}' "
                        "agent is not configured on the backend."
                    ),
                    "phase": "error",
                },
            }

        return failed_stream()

    def stream():
        event_queue: Queue[dict | object] = Queue()
        done = object()
        register_run(run_id=run_id, conversation_id=conversation_id, request_id=request_id)

        def worker() -> None:
            final_chunks: list[str] = []
            runtime_context = {
                "project_id": str(payload.get("projectId") or ""),
                "conversation_id": str(payload.get("conversationId") or ""),
                "conversation_kind": str(payload.get("conversationKind") or "channel"),
                "conversation_title": str(payload.get("conversationTitle") or ""),
                "conversation_participants": list(payload.get("conversationParticipants") or []),
                "responder_name": str(payload.get("responderName") or ""),
                "responder_job": str(payload.get("responderJob") or ""),
                "responder_description": str(payload.get("responderDescription") or ""),
                "responder_personality": str(payload.get("responderPersonality") or ""),
                "team_id": str(payload.get("teamId") or ""),
                "available_agents": list(payload.get("availableAgents") or []),
                "current_responder_ref": str(payload.get("currentResponderRef") or ""),
                "current_user_ref": next(
                    (
                        str(item.get("authorId") or "")
                        for item in reversed(messages)
                        if isinstance(item, dict) and item.get("role") == "user" and str(item.get("authorId") or "").strip()
                    ),
                    "",
                ),
            }

            try:
                with use_runtime_context(runtime_context):
                    with use_stream_emitter(event_queue.put):
                        for chunk in stream_handler(user_input, history=history):
                            if is_stop_requested(run_id):
                                dispatch_event(request_id, f"stop requested for run {run_id}")
                                break

                            text = str(chunk or "")
                            if not text:
                                continue

                            final_chunks.append(text)
                            event_queue.put(
                                {
                                    "type": "final.delta",
                                    "data": {
                                        "textDelta": text,
                                    },
                                }
                            )
                            if is_stop_requested(run_id):
                                dispatch_event(request_id, f"stop acknowledged for run {run_id}")
                                break
            except Exception as error:
                error_event(request_id, f"agent stream failed: {error}")
                traceback.print_exc()
                event_queue.put(
                    {
                        "type": "run.failed",
                        "data": {
                            "error": str(error),
                            "content": "The agent failed while generating a response.",
                            "phase": "error",
                        },
                    }
                )
                event_queue.put(done)
                unregister_run(run_id)
                return

            final_text = _strip_leading_self_identity(
                "".join(final_chunks),
                responder_name=str(payload.get("responderName") or ""),
                responder_job=str(payload.get("responderJob") or ""),
            )
            log_final_response(request_id, final_text)

            event_queue.put(
                {
                    "type": "final.completed",
                    "data": {
                        "content": final_text,
                        "phase": "final_answer",
                    },
                }
            )
            event_queue.put(
                {
                    "type": "run.completed",
                    "data": {
                        "content": final_text,
                        "phase": "final_answer",
                        "status": "stopped" if is_stop_requested(run_id) else "completed",
                        "requestedAgentRefs": [],
                        "handoffReason": "",
                        "handoffPrompt": "",
                        "imageUrl": None,
                        "videoUrl": None,
                        "runId": run_id,
                    },
                }
            )
            event_queue.put(done)
            unregister_run(run_id)

        yield {
            "type": "run.started",
            "data": {
                "runId": run_id,
                "status": "running",
            },
        }

        thread = Thread(target=worker, name=f"agent-stream-{request_id}", daemon=True)
        thread.start()

        while True:
            try:
                event = event_queue.get(timeout=0.25)
            except Empty:
                continue

            if event is done:
                break

            yield event

    return stream()


def main() -> None:
    print("Archibot CLI. Type 'exit' or 'quit' to stop.")
    agent_choice = input("Choose an agent (1 for main agent, 2 for intern, 3 for junior architect): ").strip()
    if agent_choice == "2":
        ask_func = ask_intern_stream
        print("You have chosen the intern agent.")
    elif agent_choice == "3":
        ask_func = ask_junior_stream
        print("You have chosen the junior architect agent.")
    else:
        ask_func = ask_main_stream
        print("Defaulting to main agent.")

    history: list[HumanMessage | AIMessage] = []
    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        print("\nAssistant: ", end="", flush=True)
        response_parts = []
        for chunk in ask_func(user_input, history=history):
            response_parts.append(chunk)
            print(chunk, end="", flush=True)
        print()

        response = "".join(response_parts)
        history.append(HumanMessage(content=user_input))
        history.append(AIMessage(content=response))


if __name__ == "__main__":
    main()
