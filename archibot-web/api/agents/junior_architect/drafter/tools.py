from langchain_core.tools import tool

from ...trace import emit_tool_completed, emit_tool_failed, emit_tool_started


@tool
def sun_diagram(site_location: str):
    """Draws a sun diagram for the given site location."""
    call_id = emit_tool_started("sun_diagram", args={"site_location": site_location})
    try:
        result = f"SUN Diagram for {site_location} has been completed by the drafter."
        emit_tool_completed("sun_diagram", call_id, output=result)
        return result
    except Exception as exc:
        emit_tool_failed("sun_diagram", call_id, str(exc))
        raise


tools = [sun_diagram]
