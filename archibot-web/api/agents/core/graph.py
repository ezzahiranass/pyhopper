from __future__ import annotations

import json

from langchain_core.messages import ToolMessage
from langgraph.graph import END, START, StateGraph

from .state import AgentState
from .supervisor import route_supervisor, supervisor_node
from .tools import TOOLS


def _format_tool_error(tool_name: str, tool, error: Exception) -> str:
    schema_hint = ""

    try:
        expected_args = getattr(tool, "args", None) or {}
        if expected_args:
            schema_hint = f" Expected arguments schema: {json.dumps(expected_args, ensure_ascii=True, default=str)}."
    except Exception:
        schema_hint = ""

    return (
        f"Tool '{tool_name}' failed before completing. "
        f"Error: {error}.{schema_hint} "
        "Revise the tool arguments and try again if the tool is still needed."
    )


def tools_node(state, all_tools):
    tools_by_name = {tool.name: tool for tool in all_tools}
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []
    tool_messages = []

    for tool_call in tool_calls:
        tool_name = tool_call.get("name", "")
        tool = tools_by_name.get(tool_name)
        if tool is None:
            tool_messages.append(
                ToolMessage(
                    content=f"Unknown tool '{tool_name}'.",
                    name=tool_name,
                    tool_call_id=tool_call.get("id", ""),
                )
            )
            continue

        try:
            result = tool.invoke(tool_call.get("args") or {})
            content = str(result)
        except Exception as error:
            content = _format_tool_error(tool_name, tool, error)

        tool_messages.append(
            ToolMessage(
                content=content,
                name=tool_name,
                tool_call_id=tool_call.get("id", ""),
            )
        )

    return {"messages": tool_messages}


def build_graph(system_prompt="", human_prompt="", tools=[]):
    all_tools = [*TOOLS, *(tools or [])]

    builder = StateGraph(AgentState)
    builder.add_node("supervisor", lambda state: supervisor_node(state, system_prompt, human_prompt, all_tools))
    builder.add_node("tools", lambda state: tools_node(state, all_tools))

    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "tools": "tools",
            "end": END,
        },
    )
    builder.add_edge("tools", "supervisor")

    return builder.compile()
