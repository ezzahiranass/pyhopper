from google.cloud.firestore_v1.base_query import FieldFilter

from .client import get_firestore_client


def get_team_context(team_id: str) -> dict:
    if not team_id:
        return {"error": "No team ID was provided."}

    db = get_firestore_client()
    team_doc = db.collection("teams").document(team_id).get()
    if not team_doc.exists:
        return {"error": f"Team '{team_id}' was not found."}

    team_data = team_doc.to_dict() or {}
    agent_ids = team_data.get("agentIds") or []
    project_ids = team_data.get("projectIds") or []

    agents: list[dict] = []
    for agent_id in agent_ids:
        agent_doc = db.collection("agents").document(agent_id).get()
        if not agent_doc.exists:
            continue
        agent_data = agent_doc.to_dict() or {}
        agents.append({
            "id": agent_doc.id,
            "name": str(agent_data.get("name") or ""),
            "job": str(agent_data.get("job") or agent_data.get("title") or ""),
            "description": str(agent_data.get("description") or ""),
            "personality": str(agent_data.get("personality") or ""),
            "parentId": str(agent_data.get("parentId") or ""),
        })

    users: list[dict] = []
    user_docs = db.collection("users").where(
        filter=FieldFilter("teamIds", "array_contains", team_id)
    ).stream()
    for user_doc in user_docs:
        user_data = user_doc.to_dict() or {}
        users.append({
            "ref": f"user:{user_doc.id}",
            "displayName": str(user_data.get("displayName") or ""),
            "email": str(user_data.get("email") or ""),
        })

    projects: list[dict] = []
    for project_id in project_ids:
        project_doc = db.collection("projects").document(project_id).get()
        if not project_doc.exists:
            continue
        project_data = project_doc.to_dict() or {}
        projects.append({
            "id": project_doc.id,
            "name": str(project_data.get("name") or ""),
            "description": str(project_data.get("description") or ""),
        })

    return {
        "team": {
            "id": team_doc.id,
            "name": str(team_data.get("name") or ""),
            "agentIds": agent_ids,
            "projectIds": project_ids,
        },
        "agents": agents,
        "users": users,
        "projects": projects,
        "counts": {
            "agents": len(agents),
            "users": len(users),
            "projects": len(projects),
        },
    }
