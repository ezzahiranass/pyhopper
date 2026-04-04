from typing import Sequence

from ...core.agent import Agent
from .prompts import system_prompt
from .tools import tools


def build_agent() -> Agent:
    return Agent(
        name="Omar",
        job="Site Analyzer",
        description="A site analyzer who is eager to learn and assist with various tasks.",
        tools=tools,
        system_prompt=system_prompt,
    )


def ask(user_input: str, history: Sequence | None = None) -> str:
    site_analyzer = build_agent()
    site_analyzer.work(user_input, history=history)
    try:
        response = site_analyzer.output.get("messages", [])[-1].content
        return response
    except Exception as exc:
        raise RuntimeError("Failed to get response from site analyzer.") from exc


def ask_stream(
    user_input: str,
    history: Sequence | None = None,
    *,
    trace_node: str | None = None,
    stream_final: bool = True,
):
    site_analyzer = build_agent()
    yield from site_analyzer.stream_work(
        user_input,
        history=history,
        trace_node=trace_node,
        stream_final=stream_final,
    )
