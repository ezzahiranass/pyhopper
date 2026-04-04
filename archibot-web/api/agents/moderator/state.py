from typing import TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated


class ModeratorState(TypedDict, total=False):
    request_id: str
    conversation_kind: str
    conversation_title: str
    conversation_participants: list[dict]
    messages: list[dict]
    available_agents: list[dict]
    agent_messages: Annotated[list[AnyMessage], add_messages]
    selected_agent_refs: list[str]
    tool_retry_required: bool
