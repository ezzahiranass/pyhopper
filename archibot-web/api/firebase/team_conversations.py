from google.cloud.firestore_v1.base_query import FieldFilter

from .client import get_firestore_client


def _participant_label(db, participant_ref: str) -> str:
    ref_value = str(participant_ref or "").strip()
    if ":" not in ref_value:
        return ref_value

    kind, raw_id = ref_value.split(":", 1)
    if kind == "user":
        doc = db.collection("users").document(raw_id).get()
        if doc.exists:
            data = doc.to_dict() or {}
            return str(data.get("displayName") or data.get("email") or ref_value)
    if kind == "agent":
        doc = db.collection("agents").document(raw_id).get()
        if doc.exists:
            data = doc.to_dict() or {}
            return str(data.get("name") or data.get("job") or ref_value)

    return ref_value


def list_team_conversations(team_id: str) -> dict:
    if not team_id:
        return {"error": "No team ID was provided."}

    db = get_firestore_client()
    team_doc = db.collection("teams").document(team_id).get()
    if not team_doc.exists:
        return {"error": f"Team '{team_id}' was not found."}

    team_data = team_doc.to_dict() or {}
    project_ids = team_data.get("projectIds") or []
    conversations: list[dict] = []

    for project_id in project_ids:
        project_doc = db.collection("projects").document(project_id).get()
        project_data = project_doc.to_dict() if project_doc.exists else {}
        conversation_docs = db.collection("conversations").where(
            filter=FieldFilter("projectId", "==", project_id)
        ).stream()
        for conversation_doc in conversation_docs:
            conversation_data = conversation_doc.to_dict() or {}
            kind = str(conversation_data.get("kind") or "")
            if kind not in {"channel", "group"}:
                continue

            participant_ids = conversation_data.get("participantIds") or []
            conversations.append(
                {
                    "id": conversation_doc.id,
                    "projectId": str(project_id),
                    "projectName": str((project_data or {}).get("name") or ""),
                    "kind": kind,
                    "title": str(conversation_data.get("title") or ""),
                    "participantIds": [
                        str(value) for value in participant_ids if isinstance(value, str) and value.strip()
                    ],
                    "participantNames": [
                        _participant_label(db, str(value))
                        for value in participant_ids
                        if isinstance(value, str) and value.strip()
                    ],
                    "participantCount": len(participant_ids) if isinstance(participant_ids, list) else 0,
                }
            )

    conversations.sort(key=lambda item: (item["projectId"], item["kind"], item["title"].lower()))

    return {
        "team": {
            "id": team_doc.id,
            "name": str(team_data.get("name") or ""),
            "projectIds": project_ids,
        },
        "conversations": conversations,
        "counts": {
            "projects": len(project_ids),
            "conversations": len(conversations),
            "channels": sum(1 for item in conversations if item["kind"] == "channel"),
            "groups": sum(1 for item in conversations if item["kind"] == "group"),
        },
    }
