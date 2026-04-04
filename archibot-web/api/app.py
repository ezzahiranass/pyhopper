from time import perf_counter
from uuid import uuid4


_BOOT_STARTED_AT = perf_counter()


def boot_log(stage: str) -> None:
    elapsed = perf_counter() - _BOOT_STARTED_AT
    print(f"[BOOT +{elapsed:7.3f}s] {stage}", flush=True)


boot_log("starting backend imports")

from dotenv import load_dotenv

boot_log("imported dotenv")

from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS

boot_log("imported flask")

from agents.trace import backend_event, error_event, log_http_request

boot_log("imported agents.trace")

from agents.catalog import load_job_overviews

boot_log("imported agents.catalog")

from agents.cancellation import request_stop

boot_log("imported agents.cancellation")

from agents.core.prompts import list_personalities

boot_log("imported agents.core.prompts")

from agents.moderator.main import respond as moderate_channel

boot_log("imported agents.moderator.main")

from agents.streaming import format_sse_event

boot_log("imported agents.streaming")

from agents.main import respond_stream

boot_log("imported agents.main")

from firebase.workspace import (
    write_project_brief_artifact,
    write_site_analysis_boilerplate,
    write_site_geolocation_artifact,
)
from firebase.client import get_firestore_client

boot_log("imported firebase.workspace")

load_dotenv()
boot_log("loaded environment variables")

app = Flask(__name__)
boot_log("created Flask app")
CORS(app)
boot_log("enabled CORS")


@app.get("/jobs/overviews")
def job_overviews():
    return jsonify({"jobs": load_job_overviews()})


@app.get("/personalities")
def personalities():
    return jsonify({"personalities": list_personalities()})


@app.post("/chat/respond/stream")
def chat_respond_stream():
    print("-------------------------------------------------------")
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages")
    request_id = str(payload.get("requestId") or uuid4().hex[:8])
    payload["requestId"] = request_id

    if not isinstance(messages, list) or len(messages) == 0:
        error_event(request_id, "invalid stream request: messages must be a non-empty list")
        return jsonify({"error": "messages must be a non-empty list"}), 400

    if not str(payload.get("conversationId") or "").strip():
        error_event(request_id, "invalid stream request: conversationId is required")
        return jsonify({"error": "conversationId is required"}), 400

    log_http_request(request_id, payload, messages)

    @stream_with_context
    def generate():
        for event in respond_stream(messages, payload):
            yield format_sse_event(event)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/chat/respond/stop")
def chat_respond_stop():
    payload = request.get_json(silent=True) or {}
    request_id = str(payload.get("requestId") or uuid4().hex[:8])
    run_id = str(payload.get("runId") or "").strip()
    conversation_id = str(payload.get("conversationId") or "").strip()

    if not run_id:
        error_event(request_id, "invalid stop request: runId is required")
        return jsonify({"error": "runId is required"}), 400

    stopped = request_stop(run_id, conversation_id=conversation_id)
    backend_event(
        request_id,
        f"POST /chat/respond/stop run={run_id} conversation={conversation_id or '-'} stopped={stopped}",
    )
    if not stopped:
        return jsonify({"stopped": False, "error": "run not found"}), 404

    return jsonify({"stopped": True, "runId": run_id})


@app.post("/ghosts/moderator/responders")
def ghost_moderator_responders():
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages")
    request_id = str(payload.get("requestId") or uuid4().hex[:8])
    available_agents = payload.get("availableAgents") or []

    if not isinstance(messages, list) or len(messages) == 0:
        error_event(request_id, "invalid moderator request: messages must be a non-empty list")
        return jsonify({"error": "messages must be a non-empty list"}), 400

    backend_event(
        request_id,
        (
            "POST /ghosts/moderator/responders "
            f"team={payload.get('teamId') or '-'} "
            f"candidates={len(available_agents) if isinstance(available_agents, list) else 0}"
        ),
    )

    result = moderate_channel(
        {
            "requestId": request_id,
            "conversationKind": str(payload.get("conversationKind") or "channel"),
            "conversationTitle": str(payload.get("conversationTitle") or ""),
            "conversationParticipants": payload.get("conversationParticipants") or [],
            "messages": messages,
            "availableAgents": available_agents,
        }
    )
    backend_event(request_id, f"moderator final selection={result.get('selected_agent_refs') or []}")
    return jsonify({"agentRefs": result.get("selected_agent_refs") or []})


@app.post("/projects/autorun-initial-analysis")
def autorun_initial_project_analysis():
    payload = request.get_json(silent=True) or {}
    request_id = str(payload.get("requestId") or uuid4().hex[:8])
    project_id = str(payload.get("projectId") or "").strip()

    if not project_id:
        error_event(request_id, "invalid project analysis request: projectId is required")
        return jsonify({"error": "projectId is required"}), 400

    backend_event(request_id, f"POST /projects/autorun-initial-analysis project={project_id}")

    db = get_firestore_client()
    project_ref = db.collection("projects").document(project_id)

    def _set_status(status: str):
        try:
            update = {"analysisStatus": status}
            if status == "done":
                update["analysisUpToDate"] = True
            project_ref.update(update)
        except Exception as exc:
            print(f"[autorun] WARNING could not write analysisStatus={status}: {exc}")

    _set_status("running")

    try:
        result = write_project_brief_artifact(
            project_id,
            name=str(payload.get("name") or "").strip(),
            description=str(payload.get("description") or "").strip(),
            project_type=str(payload.get("projectType") or "").strip(),
            site_coordinates=payload.get("siteCoordinates"),
            site_center=payload.get("siteCenter"),
            analysis_radius=payload.get("analysisRadius"),
        )
        if result.get("error"):
            error_event(request_id, f"project analysis failed: {result['error']}")
            _set_status("error")
            return jsonify({"error": result["error"]}), 500

        geolocation_result = write_site_geolocation_artifact(
            project_id,
            site_coordinates=payload.get("siteCoordinates"),
            site_center=payload.get("siteCenter"),
            analysis_radius=payload.get("analysisRadius"),
        )
        if geolocation_result.get("error"):
            error_event(request_id, f"site geolocation analysis failed: {geolocation_result['error']}")
            _set_status("error")
            return jsonify({"error": geolocation_result["error"]}), 500

        site_analysis_result = write_site_analysis_boilerplate(
            project_id,
            name=str(payload.get("name") or "").strip(),
            description=str(payload.get("description") or "").strip(),
            project_type=str(payload.get("projectType") or "").strip(),
            site_coordinates=payload.get("siteCoordinates"),
            site_center=payload.get("siteCenter"),
            analysis_radius=payload.get("analysisRadius"),
        )
        if not site_analysis_result.get("ok"):
            error_event(request_id, f"site analysis boilerplate failed: {site_analysis_result}")
            _set_status("error")
            return jsonify({"error": "Failed to write site analysis boilerplate.", **site_analysis_result}), 500

        _set_status("done")
        return jsonify({
            "ok": True,
            "projectBrief": result,
            "siteGeolocation": geolocation_result,
            "siteAnalysis": site_analysis_result,
        })

    except Exception as exc:
        error_event(request_id, f"autorun-initial-analysis unhandled error: {exc}")
        _set_status("error")
        raise


if __name__ == '__main__':
    # RUNNING FLASK APP
    boot_log("starting Flask development server on port 5000")
    app.run(debug=True, use_reloader=False, port=5000)
