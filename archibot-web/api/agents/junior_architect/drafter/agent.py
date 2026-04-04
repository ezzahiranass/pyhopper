from typing import Sequence

from ...core.agent import Agent
from .prompts import system_prompt
from .tools import tools


def build_agent() -> Agent:
    return Agent(
        name="Yahya",
        job="Drafter",
        description="A drafter who is eager to learn and assist with various tasks.",
        tools=tools,
        system_prompt=system_prompt,
    )


def ask(user_input: str, history: Sequence | None = None) -> str:
    drafter = build_agent()
    drafter.work(user_input, history=history)
    try:
        response = drafter.output.get("messages", [])[-1].content
        return response
    except Exception as exc:
        raise RuntimeError("Failed to get response from drafter.") from exc


def ask_stream(
    user_input: str,
    history: Sequence | None = None,
    *,
    trace_node: str | None = None,
    stream_final: bool = True,
):
    drafter = build_agent()
    yield from drafter.stream_work(
        user_input,
        history=history,
        trace_node=trace_node,
        stream_final=stream_final,
    )
