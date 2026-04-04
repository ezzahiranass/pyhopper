from __future__ import annotations

from typing import Sequence
from langchain_core.messages import AIMessage, HumanMessage

from .graph import build_graph
from .prompts import system_message, human_message
from ..trace import emit_commentary_completed, emit_commentary_delta, trace_scope




class Agent:
    def __init__(
        self,
        name: str,
        job: str,
        description: str,
        personality: str = "",
        tools=None,
        system_prompt: str = "",
    ):
        self.name = name
        self.job = job
        self.description = description
        self.personality = personality

        self.tools = tools or []
        self.system_prompt = system_message(name, job, description, system_prompt, personality)
        self.human_message = human_message(name, job)
        self.graph = build_graph(self.system_prompt, self.human_message, self.tools)
        self.output = None

    def _build_messages(self, user_input: str, history: Sequence | None = None):
        messages = list(history or [])
        messages.append(HumanMessage(content=user_input))
        return messages

    def work(self, user_input: str, history: Sequence | None = None):
        messages = self._build_messages(user_input, history=history)
        self.output = self.graph.invoke({"messages": messages})

    def stream_work(
        self,
        user_input: str,
        history: Sequence | None = None,
        *,
        trace_node: str | None = None,
        stream_final: bool = True,
    ):
        messages = self._build_messages(user_input, history=history)
        streamed_text = []

        scope_name = trace_node or self.job
        with trace_scope(scope_name):
            for chunk, metadata in self.graph.stream(
                {"messages": messages},
                stream_mode="messages",
            ):
                if metadata.get("langgraph_node") != "supervisor":
                    continue

                content = getattr(chunk, "content", "")
                if not isinstance(content, str) or not content:
                    continue

                streamed_text.append(content)
                if stream_final:
                    yield content
                else:
                    emit_commentary_delta(content)

        final_text = "".join(streamed_text)
        self.output = {"messages": [*messages, AIMessage(content=final_text)]}
        if not stream_final:
            emit_commentary_completed(final_text, status_text=f"{self.job} completed")



def ask(user_input: str, history: Sequence | None = None) -> str:
    agent = Agent(name="John", description="Architectural assistant", job="Architect")
    agent.work(user_input, history=history)
    try:
        response = agent.output.get("messages", [])[-1].content
        return response
    except Exception as exc:
        raise RuntimeError("Failed to get response from agent app.") from exc


def ask_stream(
    user_input: str,
    history: Sequence | None = None,
    *,
    trace_node: str | None = None,
    stream_final: bool = True,
):
    agent = Agent(name="John", description="Architectural assistant", job="Architect")
    yield from agent.stream_work(
        user_input,
        history=history,
        trace_node=trace_node,
        stream_final=stream_final,
    )
