import json

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool

from ..trace import tool_event
from .state import ModeratorState


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _resolve_agent_refs(selections: list[str], available_agents: list[dict]) -> list[str]:
    if not selections:
        return []

    by_ref = {agent["ref"]: agent["ref"] for agent in available_agents if agent.get("ref")}
    by_id: dict[str, list[str]] = {}
    by_name: dict[str, list[str]] = {}
    by_job: dict[str, list[str]] = {}

    for agent in available_agents:
        ref = str(agent.get("ref") or "").strip()
        if not ref:
            continue

        ref_id = ref.split(":", 1)[1] if ":" in ref else ref
        name_key = _normalize(str(agent.get("name") or ""))
        job_key = _normalize(str(agent.get("job") or ""))

        if ref_id:
            by_id.setdefault(ref_id, []).append(ref)
        if name_key:
            by_name.setdefault(name_key, []).append(ref)
        if job_key:
            by_job.setdefault(job_key, []).append(ref)

    resolved: list[str] = []
    seen = set()

    for raw_selection in selections:
        selection = str(raw_selection or "").strip()
        if not selection:
            continue

        matched_refs = []
        if selection in by_ref:
            matched_refs = [by_ref[selection]]
        else:
            normalized = _normalize(selection)
            matched_refs = by_id.get(selection, []) or by_name.get(normalized, []) or by_job.get(normalized, [])

        for ref in matched_refs:
            if ref not in seen:
                seen.add(ref)
                resolved.append(ref)

    return resolved


def _validate_agent_names(selections: list[str], available_agents: list[dict]) -> tuple[list[str], list[str]]:
    if not selections:
        return [], []

    by_name = {
        _normalize(str(agent.get("name") or "")): str(agent.get("name") or "").strip()
        for agent in available_agents
        if str(agent.get("name") or "").strip()
    }

    valid_names: list[str] = []
    invalid_names: list[str] = []

    for raw_selection in selections:
        selection = str(raw_selection or "").strip()
        if not selection:
            continue

        normalized = _normalize(selection)
        resolved_name = by_name.get(normalized)
        if resolved_name:
            valid_names.append(resolved_name)
        else:
            invalid_names.append(selection)

    return valid_names, invalid_names


def list_tools():
    @tool
    def select_responders(agent_names: list[str], rationale: str = "") -> dict:
        """Return the names of the agents that should respond to the latest channel message.
        if no agents should respond, input an empty list."""
        return {
            "agent_names": agent_names,
            "rationale": rationale.strip(),
        }

    return {
        select_responders.name: select_responders,
    }


def get_tools(state: ModeratorState) -> dict:
    tool_index = list_tools()
    last_message = state["agent_messages"][-1]
    tool_messages: list[ToolMessage] = []
    available_agents = state.get("available_agents") or []
    selected_agent_refs: list[str] = []
    tool_retry_required = False

    for tool_call in getattr(last_message, "tool_calls", []):
        tool_name = tool_call["name"]
        tool_handler = tool_index[tool_name]
        tool_result = tool_handler.invoke(tool_call.get("args", {}))
        raw_agent_names = tool_result.get("agent_names")
        raw_names = [str(value) for value in (raw_agent_names or [])]
        valid_names, invalid_names = _validate_agent_names(raw_names, available_agents)

        if raw_agent_names is None:
            tool_message_content = json.dumps(
                {
                    "error": "select_responders requires agent_names and received none.",
                    "available_agent_names": [
                        str(agent.get("name") or "").strip()
                        for agent in available_agents
                        if str(agent.get("name") or "").strip()
                    ],
                }
            )
            tool_event(
                state["request_id"],
                "moderator provided no agent_names; requesting retry.",
            )
            tool_retry_required = True
            tool_messages.append(
                ToolMessage(
                    content=tool_message_content,
                    tool_call_id=tool_call["id"],
                ),
            )
            continue

        if not raw_names:
            selected_agent_refs = []
            tool_event(
                state["request_id"],
                f"moderator selected [] from raw=[] rationale={tool_result.get('rationale') or '-'}"
            )
            tool_messages.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    tool_call_id=tool_call["id"],
                ),
            )
            continue

        if invalid_names:
            tool_message_content = json.dumps(
                {
                    "error": (
                        "These agent_names are invalid or not in the candidate list: "
                        f"{invalid_names}"
                    ),
                    "available_agent_names": [
                        str(agent.get("name") or "").strip()
                        for agent in available_agents
                        if str(agent.get("name") or "").strip()
                    ],
                }
            )
            tool_event(
                state["request_id"],
                f"moderator provided invalid agent_names={invalid_names}; requesting retry",
            )
            tool_retry_required = True
            tool_messages.append(
                ToolMessage(
                    content=tool_message_content,
                    tool_call_id=tool_call["id"],
                ),
            )
            continue

        selected_agent_refs = _resolve_agent_refs(valid_names, available_agents)
        tool_event(
            state["request_id"],
            (
                f"moderator selected {selected_agent_refs or []} "
                f"from raw={valid_names or []} "
                f"rationale={tool_result.get('rationale') or '-'}"
            ),
        )
        tool_messages.append(
            ToolMessage(
                content=json.dumps(tool_result),
                tool_call_id=tool_call["id"],
            ),
        )

    return {
        "agent_messages": tool_messages,
        "selected_agent_refs": selected_agent_refs,
        "tool_retry_required": tool_retry_required,
    }
