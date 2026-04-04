from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from .main import agent, finalize_response, prepare_messages
from .state import ModeratorState
from .tools import get_tools


def route(state: ModeratorState) -> str:
    last_message = state["agent_messages"][-1] if state["agent_messages"] else None
    if getattr(last_message, "tool_calls", None):
        return "use_tools"
    return "finish"


def route_after_tools(state: ModeratorState) -> str:
    if state.get("tool_retry_required"):
        return "agent"
    return "finish"


@lru_cache(maxsize=1)
def build_graph():
    graph_builder = StateGraph(ModeratorState)
    graph_builder.add_node("prepare", prepare_messages)
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("use_tools", get_tools)
    graph_builder.add_node("finish", finalize_response)

    graph_builder.add_edge(START, "prepare")
    graph_builder.add_edge("prepare", "agent")
    graph_builder.add_conditional_edges("agent", route)
    graph_builder.add_conditional_edges(
        "use_tools",
        route_after_tools,
        {
            "agent": "agent",
            "finish": "finish",
        },
    )
    graph_builder.add_edge("finish", END)
    return graph_builder.compile()
