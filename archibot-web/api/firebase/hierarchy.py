from __future__ import annotations

from typing import Literal

from firebase_admin import firestore

from agents.catalog import get_valid_job_titles
from .client import get_firestore_client

AgentAction = Literal["add_agent", "remove_agent"]


def _generate_agent_name(job: str, existing_names: set[str]) -> str:
    base_name = f"{job} Agent"
    if base_name not in existing_names:
        return base_name

    index = 2
    while f"{base_name} {index}" in existing_names:
        index += 1
    return f"{base_name} {index}"


def _default_agent_description(job: str) -> str:
    return f"{job} added by the manager."


def update_team_hierarchy(
    team_id: str,
    action: AgentAction,
    *,
    parent_id: str | None = None,
    agent_id: str | None = None,
    name: str | None = None,
    job: str | None = None,
    description: str | None = None,
    personality: str | None = None,
) -> dict:
    if not team_id:
        return {"error": "No team ID was provided."}

    db = get_firestore_client()
    team_ref = db.collection("teams").document(team_id)
    team_doc = team_ref.get()
    if not team_doc.exists:
        return {"error": f"Team '{team_id}' was not found."}

    team_data = team_doc.to_dict() or {}
    current_agent_ids = [str(value) for value in (team_data.get("agentIds") or []) if str(value)]
    current_agent_id_set = set(current_agent_ids)

    if action == "add_agent":
        existing_names = {
            str(agent_doc.to_dict().get("name") or "").strip()
            for agent_doc in db.collection("agents").where("teamId", "==", team_id).stream()
            if agent_doc.exists
        }
        clean_job = str(job or "").strip()
        clean_parent_id = str(parent_id or "").strip()
        valid_agent_jobs = get_valid_job_titles()

        if clean_job not in valid_agent_jobs:
            return {
                "error": (
                    "A valid job is required to add an agent. "
                    f"Allowed jobs: {', '.join(sorted(valid_agent_jobs))}."
                ),
            }
        if not clean_parent_id:
            return {"error": "A parent_id is required to add an agent."}
        if clean_parent_id not in current_agent_id_set:
            return {"error": f"Parent agent '{clean_parent_id}' was not found in team '{team_id}'."}

        clean_name = str(name or "").strip() or _generate_agent_name(clean_job, existing_names)
        clean_description = str(description or "").strip() or _default_agent_description(clean_job)
        clean_personality = str(personality or "").strip()

        agent_ref = db.collection("agents").document()
        agent_ref.set(
            {
                "teamId": team_id,
                "parentId": clean_parent_id,
                "name": clean_name,
                "job": clean_job,
                "description": clean_description,
                "personality": clean_personality,
            }
        )
        team_ref.update({"agentIds": firestore.ArrayUnion([agent_ref.id])})
        return {
            "ok": True,
            "action": action,
            "agent": {
                "id": agent_ref.id,
                "parentId": clean_parent_id,
                "name": clean_name,
                "job": clean_job,
                "description": clean_description,
                "personality": clean_personality,
            },
        }

    if action == "remove_agent":
        clean_agent_id = str(agent_id or "").strip()
        if not clean_agent_id:
            return {"error": "An agent_id is required to remove an agent."}
        if clean_agent_id not in current_agent_id_set:
            return {"error": f"Agent '{clean_agent_id}' was not found in team '{team_id}'."}

        agent_docs = {
            agent_doc.id: (agent_doc.to_dict() or {})
            for agent_doc in db.collection("agents").where("teamId", "==", team_id).stream()
        }
        if clean_agent_id not in agent_docs:
            return {"error": f"Agent '{clean_agent_id}' does not exist in Firestore for team '{team_id}'."}

        ids_to_remove = {clean_agent_id}
        changed = True
        while changed:
            changed = False
            for existing_agent_id, agent_data in agent_docs.items():
                parent_value = str(agent_data.get("parentId") or "")
                if parent_value in ids_to_remove and existing_agent_id not in ids_to_remove:
                    ids_to_remove.add(existing_agent_id)
                    changed = True

        batch = db.batch()
        for remove_id in ids_to_remove:
            batch.delete(db.collection("agents").document(remove_id))
        batch.update(team_ref, {"agentIds": firestore.ArrayRemove(sorted(ids_to_remove))})
        batch.commit()

        return {
            "ok": True,
            "action": action,
            "removedAgentIds": sorted(ids_to_remove),
        }

    return {"error": f"Unsupported action '{action}'."}
