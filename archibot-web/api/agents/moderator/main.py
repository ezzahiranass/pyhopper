from langchain_core.messages import HumanMessage, SystemMessage

from ..core.config import get_llm
from .prompts import build_user_message, get_system_prompt
from .state import ModeratorState
from .tools import list_tools


def build_state(payload: dict) -> ModeratorState:
    return {
        "request_id": str(payload.get("request_id") or payload.get("requestId") or ""),
        "conversation_kind": str(payload.get("conversation_kind") or payload.get("conversationKind") or "channel"),
        "conversation_title": str(payload.get("conversation_title") or payload.get("conversationTitle") or ""),
        "conversation_participants": [
            {
                "ref": str(item.get("ref") or ""),
                "name": str(item.get("name") or item.get("label") or "Unknown"),
                "job": str(item.get("job") or ""),
                "kind": str(item.get("kind") or ""),
            }
            for item in (payload.get("conversation_participants") or payload.get("conversationParticipants") or [])
            if isinstance(item, dict) and str(item.get("ref") or "").strip()
        ],
        "messages": [
            {
                "role": "assistant" if item.get("role") == "assistant" else "user",
                "author": str(item.get("author") or "Unknown"),
                "author_id": str(item.get("authorId") or ""),
                "author_job": str(item.get("authorJob") or ""),
                "author_kind": str(item.get("authorKind") or ""),
                "content": str(item.get("content") or ""),
            }
            for item in (payload.get("messages") or [])
            if isinstance(item, dict) and str(item.get("content") or "").strip()
        ],
        "available_agents": [
            {
                "ref": str(item.get("ref") or ""),
                "name": str(item.get("name") or ""),
                "job": str(item.get("job") or ""),
                "description": str(item.get("description") or ""),
            }
            for item in (payload.get("available_agents") or payload.get("availableAgents") or [])
            if isinstance(item, dict) and str(item.get("ref") or "").strip()
        ],
        "selected_agent_refs": [],
        "tool_retry_required": False,
    }


def prepare_messages(state: ModeratorState) -> dict:
    return {
        "agent_messages": [
            SystemMessage(content=get_system_prompt(state)),
            HumanMessage(content=build_user_message(state)),
        ],
    }


def agent(state: ModeratorState) -> dict:
    tools = list(list_tools().values())
    model = get_llm().bind_tools(tools)
    result = model.invoke(state["agent_messages"])
    return {"agent_messages": [result]}


def finalize_response(state: ModeratorState) -> dict:
    return {
        "selected_agent_refs": state.get("selected_agent_refs", []),
    }


def respond(payload: dict):
    from .graph import build_graph

    return build_graph().invoke(build_state(payload))
