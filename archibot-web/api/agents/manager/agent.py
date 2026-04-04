from typing import Sequence

from ..core.agent import Agent
from ..runtime import resolve_runtime_identity
from .prompts import system_prompt
from .tools import tools


def build_agent() -> Agent:
    identity = resolve_runtime_identity()
    return Agent(
        name=identity["name"],
        job=identity["job"],
        description=identity["description"],
        personality=identity["personality"],
        tools=tools,
        system_prompt=system_prompt,
    )


def ask(user_input: str, history: Sequence | None = None) -> str:
    manager = build_agent()
    manager.work(user_input, history=history)
    try:
        response = manager.output.get("messages", [])[-1].content
        return response
    except Exception as exc:
        raise RuntimeError("Failed to get response from manager.") from exc


def ask_stream(
    user_input: str,
    history: Sequence | None = None,
    *,
    trace_node: str | None = None,
    stream_final: bool = True,
):
    manager = build_agent()
    yield from manager.stream_work(
        user_input,
        history=history,
        trace_node=trace_node,
        stream_final=stream_final,
    )
