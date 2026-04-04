from langchain_core.tools import tool

from ...runtime import get_runtime_context
from ...trace import emit_tool_completed, emit_tool_failed, emit_tool_started
from firebase.workspace import write_subdomain_content

AREA_SLUG = "site-analysis"


def _get_project_id() -> str:
    ctx = get_runtime_context()
    project_id = str(ctx.get("project_id") or "").strip()
    print(f"[site_analyzer] runtime context keys: {list(ctx.keys())}")
    print(f"[site_analyzer] project_id={project_id!r}")
    return project_id


@tool
def sun_analysis(site_location: str, findings: str):
    """Performs solar analysis for the site.
    Call this with the actual analysis findings as the `findings` argument —
    a detailed paragraph covering sun path, solar exposure, shading, and seasonal variation.
    """
    call_id = emit_tool_started("sun_analysis", args={"site_location": site_location})
    try:
        emit_tool_completed("sun_analysis", call_id, output=findings)

        project_id = _get_project_id()
        if project_id:
            result = write_subdomain_content(
                project_id=project_id,
                area_slug=AREA_SLUG,
                subdomain_slug="sun",
                content=findings,
            )
            print(f"[site_analyzer] sun write result: {result}")
        else:
            print("[site_analyzer] sun: skipping Firestore write (no project_id)")

        return findings
    except Exception as exc:
        emit_tool_failed("sun_analysis", call_id, str(exc))
        raise


@tool
def wind_analysis(site_location: str, findings: str):
    """Performs wind analysis for the site.
    Call this with the actual analysis findings as the `findings` argument —
    a detailed paragraph covering prevailing wind direction, speed, seasonal patterns, and shelter considerations.
    """
    call_id = emit_tool_started("wind_analysis", args={"site_location": site_location})
    try:
        emit_tool_completed("wind_analysis", call_id, output=findings)

        project_id = _get_project_id()
        if project_id:
            result = write_subdomain_content(
                project_id=project_id,
                area_slug=AREA_SLUG,
                subdomain_slug="wind",
                content=findings,
            )
            print(f"[site_analyzer] wind write result: {result}")
        else:
            print("[site_analyzer] wind: skipping Firestore write (no project_id)")

        return findings
    except Exception as exc:
        emit_tool_failed("wind_analysis", call_id, str(exc))
        raise


@tool
def topography_analysis(site_location: str, findings: str):
    """Performs topography analysis for the site.
    Call this with the actual analysis findings as the `findings` argument —
    a detailed paragraph covering terrain, slopes, elevation changes, drainage, and landform implications.
    """
    call_id = emit_tool_started("topography_analysis", args={"site_location": site_location})
    try:
        emit_tool_completed("topography_analysis", call_id, output=findings)

        project_id = _get_project_id()
        if project_id:
            result = write_subdomain_content(
                project_id=project_id,
                area_slug=AREA_SLUG,
                subdomain_slug="topography",
                content=findings,
            )
            print(f"[site_analyzer] topography write result: {result}")
        else:
            print("[site_analyzer] topography: skipping Firestore write (no project_id)")

        return findings
    except Exception as exc:
        emit_tool_failed("topography_analysis", call_id, str(exc))
        raise


tools = [sun_analysis, wind_analysis, topography_analysis]
