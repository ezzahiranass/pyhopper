from typing import cast

from langchain_core.tools import tool

from firebase.hierarchy import AgentAction, update_team_hierarchy

from ..runtime import get_runtime_context
from ..trace import emit_tool_completed, emit_tool_failed, emit_tool_started


@tool
def hire_agent(
    parent_id: str,
    job: str,
    name: str = "",
    description: str = "",
    personality: str = "",
) -> dict:
    """Hire a new agent under an existing parent agent in the current team."""
    call_id = emit_tool_started(
        "hire_agent",
        args={
            "parent_id": parent_id,
            "job": job,
            "name": name,
            "description": description,
            "personality": personality,
        },
    )
    runtime = get_runtime_context()
    team_id = str(runtime.get("team_id") or "").strip()

    if not team_id:
        result = {"error": "No active team ID is available in the current runtime context."}
        emit_tool_failed("hire_agent", call_id, result["error"])
        return result

    result = update_team_hierarchy(
        team_id,
        action=cast(AgentAction, "add_agent"),
        parent_id=str(parent_id or "").strip() or None,
        job=str(job or "").strip() or None,
        name=str(name or "").strip() or None,
        description=str(description or "").strip() or None,
        personality=str(personality or "").strip() or None,
    )
    if result.get("error"):
        emit_tool_failed("hire_agent", call_id, str(result.get("error")))
        return result

    emit_tool_completed("hire_agent", call_id, output=result)
    return result


@tool
def fire_agent(agent_id: str) -> dict:
    """Remove an existing agent and its subtree from the current team."""
    call_id = emit_tool_started("fire_agent", args={"agent_id": agent_id})
    runtime = get_runtime_context()
    team_id = str(runtime.get("team_id") or "").strip()

    if not team_id:
        result = {"error": "No active team ID is available in the current runtime context."}
        emit_tool_failed("fire_agent", call_id, result["error"])
        return result

    result = update_team_hierarchy(
        team_id,
        action=cast(AgentAction, "remove_agent"),
        agent_id=str(agent_id or "").strip() or None,
    )
    if result.get("error"):
        emit_tool_failed("fire_agent", call_id, str(result.get("error")))
        return result

    emit_tool_completed("fire_agent", call_id, output=result)
    return result


tools = [hire_agent, fire_agent]
