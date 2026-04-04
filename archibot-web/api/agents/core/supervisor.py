from __future__ import annotations

from .config import get_llm
from .tools import TOOLS
from langchain_core.messages import SystemMessage, HumanMessage


def supervisor_node(state, system_prompt, human_prompt, tools):
    
    llm = get_llm().bind_tools(tools)
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            *state["messages"],
            HumanMessage(content=human_prompt),
        ]
    )
    return {"messages": [response]}


def route_supervisor(state) -> str:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return "end"
