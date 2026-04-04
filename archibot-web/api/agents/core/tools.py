from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen

from langchain_core.tools import tool
from firebase.conversations import send_conversation_message, upsert_conversation
from firebase.team_context import get_team_context
from firebase.team_conversations import list_team_conversations
from ..trace import emit_tool_completed, emit_tool_failed, emit_tool_started
from ..runtime import get_runtime_context


def _normalize_name(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _resolve_participant_names(team_context: dict, participant_names: list[str]) -> tuple[list[str], list[str], list[str]]:
    resolved_refs: list[str] = []
    missing_names: list[str] = []
    ambiguous_names: list[str] = []

    lookup: dict[str, list[str]] = {}
    for user in team_context.get("users") or []:
        label = str(user.get("displayName") or "").strip()
        ref = str(user.get("ref") or "").strip()
        if label and ref:
            lookup.setdefault(_normalize_name(label), []).append(ref)

    for agent in team_context.get("agents") or []:
        label = str(agent.get("name") or "").strip()
        agent_id = str(agent.get("id") or "").strip()
        if label and agent_id:
            lookup.setdefault(_normalize_name(label), []).append(f"agent:{agent_id}")

    for raw_name in participant_names:
        normalized_name = _normalize_name(raw_name)
        if not normalized_name:
            continue

        exact_matches = lookup.get(normalized_name, [])
        matches = exact_matches

        if not matches:
            fuzzy_matches = [
                ref
                for label, refs in lookup.items()
                if normalized_name in label or label in normalized_name
                for ref in refs
            ]
            matches = sorted(set(fuzzy_matches))

        if len(matches) == 1:
            resolved_refs.append(matches[0])
        elif len(matches) > 1:
            ambiguous_names.append(str(raw_name))
        else:
            missing_names.append(str(raw_name))

    return sorted(set(resolved_refs)), missing_names, ambiguous_names

@tool
def web_search(query: str) -> str:
    """Search the web with Tavily and return a compact summary."""
    call_id = emit_tool_started("web_search", args={"query": query})
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        result = "Web search failed: missing TAVILY_API_KEY."
        emit_tool_failed("web_search", call_id, result)
        return result

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 5,
        "include_answer": True,
        "include_raw_content": False,
    }
    request = Request(
        "https://api.tavily.com/search",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        result = f"Web search failed: {exc}"
        emit_tool_failed("web_search", call_id, result)
        return result

    answer = payload.get("answer", "").strip()
    results = payload.get("results", [])
    lines = []
    if answer:
        lines.append(f"Answer: {answer}")

    for item in results[:5]:
        title = item.get("title", "Untitled")
        content = item.get("content", "").strip()
        url = item.get("url", "")
        snippet = content[:300] + ("..." if len(content) > 300 else "")
        lines.append(f"{title}: {snippet} ({url})")

    if lines:
        result = "\n".join(lines)
        emit_tool_completed("web_search", call_id, output=result)
        return result

    result = "No useful search result found."
    emit_tool_completed("web_search", call_id, output=result)
    return result


@tool
def view_company_info(query: str = "all") -> dict:
    """Return company/team information for the active team.
    query can be:
    - 'studio_info' for team members and studio details
    - 'projects_info' for ongoing projects
    - 'conversations' for existing channels/groups and their conversation ids
    - 'all' for everything
    """
    call_id = emit_tool_started("view_company_info", args={"query": query})
    runtime = get_runtime_context()
    team_id = str(runtime.get("team_id") or "").strip()
    normalized_query = str(query or "all").strip().lower()

    if not team_id:
        result = {"error": "No active team ID is available in the current runtime context."}
        emit_tool_failed("view_company_info", call_id, result["error"])
        return result

    context_result = get_team_context(team_id)
    if context_result.get("error"):
        emit_tool_failed("view_company_info", call_id, str(context_result.get("error")))
        return context_result

    studio_info = {
        "team": context_result.get("team"),
        "agents": context_result.get("agents"),
        "users": context_result.get("users"),
        "counts": {
            "agents": (context_result.get("counts") or {}).get("agents", 0),
            "users": (context_result.get("counts") or {}).get("users", 0),
        },
    }
    projects_info = {
        "team": context_result.get("team"),
        "projects": context_result.get("projects"),
        "counts": {
            "projects": (context_result.get("counts") or {}).get("projects", 0),
        },
    }

    if normalized_query in {"studio", "studio_info", "team", "members"}:
        result = {
            "query": "studio_info",
            "studio_info": studio_info,
        }
        emit_tool_completed("view_company_info", call_id, output=result)
        return result

    if normalized_query in {"projects", "projects_info", "project"}:
        result = {
            "query": "projects_info",
            "projects_info": projects_info,
        }
        emit_tool_completed("view_company_info", call_id, output=result)
        return result

    if normalized_query in {"conversations", "conversation", "channels", "groups"}:
        conversations_result = list_team_conversations(team_id)
        if conversations_result.get("error"):
            emit_tool_failed("view_company_info", call_id, str(conversations_result.get("error")))
            return conversations_result
        result = {
            "query": "conversations",
            "conversations": conversations_result,
        }
        emit_tool_completed("view_company_info", call_id, output=result)
        return result

    if normalized_query not in {"all", ""}:
        result = {
            "error": (
                "Unsupported query. Use one of: "
                "'studio_info', 'projects_info', 'conversations', or 'all'."
            )
        }
        emit_tool_failed("view_company_info", call_id, result["error"])
        return result

    conversations_result = list_team_conversations(team_id)
    if conversations_result.get("error"):
        emit_tool_failed("view_company_info", call_id, str(conversations_result.get("error")))
        return conversations_result

    result = {
        "query": "all",
        "studio_info": studio_info,
        "projects_info": projects_info,
        "conversations": conversations_result,
    }

    emit_tool_completed("view_company_info", call_id, output=result)
    return result


@tool
def send_message(
    conversation_title: str = "",
    message: str = "",
    participants: list[str] | None = None,
    conversation_type: str = "",
) -> dict:
    """Send a message into a channel or group conversation using only names and titles.
    a channel by definition has the whole team, a group has specific participants.
    use participant names. always set the conversation title. if sending to an existing channel, name should be exact match. use view_company_info.
    Use conversation_type='channel' or conversation_type='group' explicitly.
    """
    print(
        "send_message called with "
        f"conversation_title='{conversation_title}', message='{message}', "
        f"participants={participants}, conversation_type='{conversation_type}'"
    )
    call_id = emit_tool_started(
        "send_message",
        args={
            "conversation_title": conversation_title,
            "message": message,
            "participants": participants,
            "conversation_type": conversation_type,
        },
    )
    runtime = get_runtime_context()
    project_id = str(runtime.get("project_id") or "").strip()
    current_conversation_id = str(runtime.get("conversation_id") or "").strip()
    created_by = str(runtime.get("current_responder_ref") or "").strip()
    author_name = str(runtime.get("responder_name") or "").strip() or "Agent"
    current_user_ref = str(runtime.get("current_user_ref") or "").strip()
    title_value = str(conversation_title or "").strip()
    participant_names = [str(value).strip() for value in (participants or []) if str(value).strip()]
    conversation_kind = str(conversation_type or "").strip().lower()
    message_text = str(message or "").strip()

    if not project_id:
        result = {"error": "No active project ID is available in the current runtime context."}
        emit_tool_failed("send_message", call_id, result["error"])
        return result

    if conversation_kind not in {"group", "channel"}:
        result = {"error": "conversation_type must be either 'group' or 'channel'."}
        emit_tool_failed("send_message", call_id, result["error"])
        return result

    if not message_text:
        result = {"error": "A non-empty message is required."}
        emit_tool_failed("send_message", call_id, result["error"])
        return result

    if not title_value and not participant_names:
        result = {"error": "Provide at least a conversation_title or one or more participant names."}
        emit_tool_failed("send_message", call_id, result["error"])
        return result

    team_context = get_team_context(str(runtime.get("team_id") or "").strip())
    if team_context.get("error"):
        emit_tool_failed("send_message", call_id, str(team_context.get("error")))
        return team_context

    normalized_participants, missing_names, ambiguous_names = _resolve_participant_names(team_context, participant_names)
    if missing_names:
        result = {
            "error": (
                f"These participant names could not be resolved: {missing_names}. "
                "Use view_company_info(query='studio_info') to inspect the exact names before retrying."
            )
        }
        emit_tool_failed("send_message", call_id, result["error"])
        return result
    if ambiguous_names:
        result = {
            "error": (
                f"These participant names are ambiguous: {ambiguous_names}. "
                "Use more specific full names from view_company_info(query='studio_info')."
            )
        }
        emit_tool_failed("send_message", call_id, result["error"])
        return result

    if current_user_ref:
        normalized_participants.append(current_user_ref)
    normalized_participants = sorted(set(normalized_participants))

    conversation_result = upsert_conversation(
        project_id=project_id,
        action="upsert",
        kind=conversation_kind,
        title=title_value,
        participant_refs=normalized_participants,
        created_by=created_by,
    )
    print(f"send_message with participants {participant_names} resolved to {normalized_participants} resulted in {conversation_result}")
    if conversation_result.get("error"):
        emit_tool_failed("send_message", call_id, str(conversation_result.get("error")))
        return conversation_result

    result: dict = {
        "conversation": conversation_result.get("conversation"),
        "conversationAction": conversation_result.get("action"),
        "message": None,
    }

    resolved_conversation = conversation_result.get("conversation") or {}
    resolved_conversation_id = str(resolved_conversation.get("id") or "").strip()

    if current_conversation_id and resolved_conversation_id == current_conversation_id:
        result = {
            **result,
            "error": "We are already in this conversation. Respond directly instead of using send_message.",
        }
        emit_tool_failed("send_message", call_id, result["error"])
        return result

    message_result = send_conversation_message(
        conversation_id=resolved_conversation_id,
        author_id=created_by,
        author_name=author_name,
        content=message_text,
    )
    if message_result.get("error"):
        emit_tool_failed("send_message", call_id, str(message_result.get("error")))
        return {
            **result,
            "error": str(message_result.get("error")),
        }
    result["message"] = message_result.get("message")

    emit_tool_completed("send_message", call_id, output=result)
    return result


TOOLS = [web_search, view_company_info, send_message]
