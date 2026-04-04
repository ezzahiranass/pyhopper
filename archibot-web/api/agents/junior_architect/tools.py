from langchain_core.tools import tool

from ..trace import (
    emit_commentary_completed,
    emit_tool_completed,
    emit_tool_failed,
    emit_tool_started,
    trace_scope,
)
from .drafter.agent import ask as ask_drafter
from .drafter.agent import build_agent as build_drafter_agent
from .site_analyzer.agent import ask as ask_site_analyzer
from .site_analyzer.agent import build_agent as build_site_analyzer_agent


@tool
def site_analysis(site_location: str):
    """Performs site analysis."""
    with trace_scope("site_analysis"):
        emit_commentary_completed(
            f"Delegating site analysis for {site_location}.",
            status_text="Running Site Analysis",
        )
        call_id = emit_tool_started("site_analysis", args={"site_location": site_location})

        try:
            site_analyzer = build_site_analyzer_agent()
            list(
                site_analyzer.stream_work(
                    f"{site_location}.",
                    trace_node="site_analyzer",
                    stream_final=False,
                )
            )
            analysis_result = str(site_analyzer.output.get("messages", [])[-1].content or "").strip()
            if not analysis_result:
                analysis_result = ask_site_analyzer(f"{site_location}.")

            emit_tool_completed("site_analysis", call_id, output=analysis_result)
            return analysis_result
        except Exception as exc:
            emit_tool_failed("site_analysis", call_id, str(exc))
            raise


@tool
def draft(instructions: str):
    """Drafts a building based on the given instructions."""
    with trace_scope("draft"):
        emit_commentary_completed(
            f"Delegating drafting task for {instructions}.",
            status_text="Running Drafting",
        )
        call_id = emit_tool_started("draft", args={"instructions": instructions})

        try:
            drafter = build_drafter_agent()
            list(
                drafter.stream_work(
                    f"{instructions}.",
                    trace_node="drafter",
                    stream_final=False,
                )
            )
            draft_result = str(drafter.output.get("messages", [])[-1].content or "").strip()
            if not draft_result:
                draft_result = ask_drafter(f"{instructions}.")

            emit_tool_completed("draft", call_id, output=draft_result)
            return draft_result
        except Exception as exc:
            emit_tool_failed("draft", call_id, str(exc))
            raise


tools = [site_analysis, draft]
