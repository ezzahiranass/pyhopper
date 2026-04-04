from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from .client import get_firestore_client


import re

_REF_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*:[A-Za-z0-9_-]{6,}$")


def _participant_field_key(ref: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", str(ref or ""))


def _participant_counter_seed(participant_refs: list[str], initial_value: int = 0) -> dict[str, int]:
    return {
        _participant_field_key(ref): initial_value
        for ref in _normalize_participant_refs(participant_refs)
    }

def _validate_participant_refs(participant_refs: list[str]) -> list[str]:
    """Return a list of refs that don't look like valid 'type:id' refs."""
    return [ref for ref in participant_refs if not _REF_PATTERN.match(str(ref).strip())]


def _normalize_participant_refs(participant_refs: list[str]) -> list[str]:
    cleaned = [str(value).strip() for value in participant_refs if str(value).strip()]
    return sorted(set(cleaned))


def _find_group_by_exact_participants(db, project_id: str, participant_refs: list[str]):
    normalized_target = _normalize_participant_refs(participant_refs)
    if not project_id or not normalized_target:
        return None

    group_docs = (
        db.collection("conversations")
        .where(filter=FieldFilter("projectId", "==", project_id))
        .where(filter=FieldFilter("kind", "==", "group"))
        .stream()
    )

    for conversation_doc in group_docs:
        conversation_data = conversation_doc.to_dict() or {}
        existing_refs = _normalize_participant_refs(conversation_data.get("participantIds") or [])
        if existing_refs == normalized_target:
            return conversation_doc

    return None


def _resolve_existing_ref(db, ref: str) -> tuple[str | None, str | None]:
    cleaned_ref = str(ref or "").strip()
    if not cleaned_ref or ":" not in cleaned_ref:
        return None, cleaned_ref

    ref_type, ref_id = cleaned_ref.split(":", 1)
    primary_collection = "users" if ref_type == "user" else "agents" if ref_type == "agent" else ""
    alternate_collection = "agents" if primary_collection == "users" else "users" if primary_collection == "agents" else ""

    if not primary_collection:
        return None, cleaned_ref

    if db.collection(primary_collection).document(ref_id).get().exists:
        return cleaned_ref, None

    if alternate_collection and db.collection(alternate_collection).document(ref_id).get().exists:
        corrected_type = "agent" if alternate_collection == "agents" else "user"
        return f"{corrected_type}:{ref_id}", None

    return None, cleaned_ref


def _resolve_existing_refs(db, refs: list[str]) -> tuple[list[str], list[str]]:
    resolved: list[str] = []
    missing: list[str] = []

    for ref in refs:
        corrected_ref, missing_ref = _resolve_existing_ref(db, ref)
        if corrected_ref:
            resolved.append(corrected_ref)
        elif missing_ref:
            missing.append(missing_ref)

    return resolved, missing


def upsert_conversation(
    project_id: str,
    action: str,
    kind: str,
    title: str,
    participant_refs: list[str],
    created_by: str = "",
    conversation_id: str = "",
) -> dict:
    if not project_id:
        return {"error": "No project ID was provided."}
    if action not in {"create", "update", "upsert"}:
        return {"error": "action must be either 'create', 'update', or 'upsert'."}
    if kind not in {"channel", "group"}:
        return {"error": "kind must be either 'channel' or 'group'."}

    creator_ref = str(created_by or "").strip()
    refs_to_validate = list(participant_refs)
    if creator_ref:
        refs_to_validate.append(creator_ref)

    invalid_refs = _validate_participant_refs(refs_to_validate)
    if invalid_refs:
        return {
            "error": (
                f"Invalid participant refs: {invalid_refs}. "
                "Each ref must be in 'type:id' format where id is the actual system ID (e.g. 'user:abc123', 'agent:def456'). "
                "Use view_company_info to look up the correct refs before retrying."
            )
        }

    db = get_firestore_client()
    resolved_refs, missing_refs = _resolve_existing_refs(db, refs_to_validate)
    if missing_refs:
        return {
            "error": (
                f"These participant refs do not exist in Firestore: {missing_refs}. "
                "The id may be wrong, or the prefix may not match any real user/agent document. "
                "Use view_company_info to look up the correct refs before retrying."
            )
        }

    normalized_resolved_refs = _normalize_participant_refs(resolved_refs)
    resolved_creator_ref = creator_ref
    if creator_ref and normalized_resolved_refs:
        if creator_ref in normalized_resolved_refs:
            resolved_creator_ref = creator_ref
        else:
            creator_id = creator_ref.split(":", 1)[1] if ":" in creator_ref else ""
            resolved_creator_ref = next(
                (ref for ref in normalized_resolved_refs if ref.endswith(f":{creator_id}")),
                creator_ref,
            )

    normalized_participants = _normalize_participant_refs(
        [ref for ref in normalized_resolved_refs if ref != resolved_creator_ref]
        + ([resolved_creator_ref] if resolved_creator_ref else [])
    )
    if not normalized_participants:
        return {"error": "At least one participant ref is required."}

    raw_title_value = str(title or "").strip()
    has_explicit_title = bool(raw_title_value)
    title_value = raw_title_value or "Untitled conversation"

    if action == "create":
        ref = db.collection("conversations").document()
        payload = {
            "projectId": project_id,
            "kind": kind,
            "title": title_value,
            "participantIds": normalized_participants,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "lastMessageAt": firestore.SERVER_TIMESTAMP,
            "createdBy": str(resolved_creator_ref or "") or None,
            "dmKey": None,
            "typingParticipantRefs": [],
            "unreadCountByParticipant": _participant_counter_seed(normalized_participants),
            "lastSeenAtByParticipant": _participant_counter_seed(normalized_participants),
        }
        ref.set(payload)
        return {
            "action": "created",
            "conversation": {
                "id": ref.id,
                "projectId": project_id,
                "kind": kind,
                "title": title_value,
                "participantIds": normalized_participants,
                "createdBy": payload["createdBy"],
            },
        }

    if action == "upsert":
        if conversation_id:
            ref = db.collection("conversations").document(conversation_id)
            doc = ref.get()
            if doc.exists:
                current_data = doc.to_dict() or {}
                current_participants = _normalize_participant_refs(current_data.get("participantIds") or [])
                merged_participants = sorted(set(current_participants + normalized_participants))
                current_kind = str(current_data.get("kind") or "group")
                if kind and kind != current_kind:
                    return {
                        "error": (
                            f"Conversation '{conversation_id}' is a {current_kind}, not a {kind}. "
                            "Use the matching conversation_type."
                        )
                    }
                next_kind = current_kind
                next_title = raw_title_value if has_explicit_title else str(current_data.get("title") or "Untitled conversation")
                ref.update(
                    {
                        "kind": next_kind,
                        "title": next_title,
                        "participantIds": merged_participants,
                        "updatedAt": firestore.SERVER_TIMESTAMP,
                    }
                )
                return {
                    "action": "updated",
                    "conversation": {
                        "id": ref.id,
                        "projectId": str(current_data.get("projectId") or project_id),
                        "kind": next_kind,
                        "title": next_title,
                        "participantIds": merged_participants,
                        "createdBy": current_data.get("createdBy"),
                    },
                }

        if kind == "group":
            participant_match = _find_group_by_exact_participants(db, project_id, normalized_participants)
            if participant_match is not None:
                current_data = participant_match.to_dict() or {}
                ref = participant_match.reference
                next_title = raw_title_value if has_explicit_title else str(current_data.get("title") or "Untitled conversation")
                ref.update(
                    {
                        "title": next_title,
                        "updatedAt": firestore.SERVER_TIMESTAMP,
                    }
                )
                return {
                    "action": "updated",
                    "conversation": {
                        "id": ref.id,
                        "projectId": str(current_data.get("projectId") or project_id),
                        "kind": "group",
                        "title": next_title,
                        "participantIds": _normalize_participant_refs(current_data.get("participantIds") or []),
                        "createdBy": current_data.get("createdBy"),
                    },
                }

        query = (
            db.collection("conversations")
            .where(filter=FieldFilter("projectId", "==", project_id))
            .where(filter=FieldFilter("kind", "==", kind))
            .where(filter=FieldFilter("title", "==", title_value))
        )
        docs = list(query.limit(1).stream())
        if docs:
            doc = docs[0]
            ref = doc.reference
            current_data = doc.to_dict() or {}
            current_participants = _normalize_participant_refs(current_data.get("participantIds") or [])
            merged_participants = sorted(set(current_participants + normalized_participants))
            next_kind = str(kind or current_data.get("kind") or "group")
            next_title = raw_title_value if has_explicit_title else str(current_data.get("title") or "Untitled conversation")
            ref.update(
                {
                    "kind": next_kind,
                    "title": next_title,
                    "participantIds": merged_participants,
                    "updatedAt": firestore.SERVER_TIMESTAMP,
                }
            )
            return {
                "action": "updated",
                "conversation": {
                    "id": ref.id,
                    "projectId": str(current_data.get("projectId") or project_id),
                    "kind": next_kind,
                    "title": next_title,
                    "participantIds": merged_participants,
                    "createdBy": current_data.get("createdBy"),
                },
            }

        action = "create"

    if action == "create":
        ref = db.collection("conversations").document()
        payload = {
            "projectId": project_id,
            "kind": kind,
            "title": title_value,
            "participantIds": normalized_participants,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "lastMessageAt": firestore.SERVER_TIMESTAMP,
            "createdBy": str(resolved_creator_ref or "") or None,
            "dmKey": None,
            "typingParticipantRefs": [],
            "unreadCountByParticipant": _participant_counter_seed(normalized_participants),
            "lastSeenAtByParticipant": _participant_counter_seed(normalized_participants),
        }
        ref.set(payload)
        return {
            "action": "created",
            "conversation": {
                "id": ref.id,
                "projectId": project_id,
                "kind": kind,
                "title": title_value,
                "participantIds": normalized_participants,
                "createdBy": payload["createdBy"],
            },
        }

    if conversation_id:
        ref = db.collection("conversations").document(conversation_id)
        doc = ref.get()
    else:
        query = (
            db.collection("conversations")
            .where(filter=FieldFilter("projectId", "==", project_id))
            .where(filter=FieldFilter("kind", "==", kind))
            .where(filter=FieldFilter("title", "==", title_value))
        )
        docs = list(query.limit(1).stream())
        if not docs:
            return {"error": "No matching conversation was found to update."}
        doc = docs[0]
        ref = doc.reference

    if not doc.exists:
        return {"error": f"Conversation '{conversation_id}' was not found."}

    current_data = doc.to_dict() or {}
    current_participants = _normalize_participant_refs(current_data.get("participantIds") or [])
    merged_participants = sorted(set(current_participants + normalized_participants))
    next_kind = str(kind or current_data.get("kind") or "group")
    next_title = raw_title_value if has_explicit_title else str(current_data.get("title") or "Untitled conversation")

    ref.update(
        {
            "kind": next_kind,
            "title": next_title,
            "participantIds": merged_participants,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
    )

    return {
        "action": "updated",
        "conversation": {
            "id": ref.id,
            "projectId": str(current_data.get("projectId") or project_id),
            "kind": next_kind,
            "title": next_title,
            "participantIds": merged_participants,
            "createdBy": current_data.get("createdBy"),
        },
    }


def send_conversation_message(
    conversation_id: str,
    author_id: str,
    author_name: str,
    content: str,
) -> dict:
    if not conversation_id:
        return {"error": "A conversation_id is required to send a message."}

    message_text = str(content or "").strip()
    if not message_text:
        return {"error": "A non-empty message is required to send a conversation message."}

    author_ref = str(author_id or "").strip()
    author_label = str(author_name or "").strip() or "Unknown"
    if not author_ref:
        return {"error": "An author_id is required to send a conversation message."}

    db = get_firestore_client()
    conversation_ref = db.collection("conversations").document(conversation_id)
    conversation_doc = conversation_ref.get()
    if not conversation_doc.exists:
        return {"error": f"Conversation '{conversation_id}' was not found."}

    message_ref = conversation_ref.collection("messages").document()
    message_ref.set(
        {
            "authorId": author_ref,
            "authorName": author_label,
            "content": message_text,
            "imageUrl": None,
            "videoUrl": None,
            "thoughtProcess": None,
            "phase": None,
            "runId": None,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "seenBy": [author_ref],
        }
    )
    participant_refs = _normalize_participant_refs(conversation_doc.to_dict().get("participantIds") or [])
    unread_updates = {
        f"unreadCountByParticipant.{_participant_field_key(participant_ref)}": firestore.Increment(1)
        for participant_ref in participant_refs
        if participant_ref != author_ref
    }
    conversation_ref.update(
        {
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "lastMessageAt": firestore.SERVER_TIMESTAMP,
            **unread_updates,
        }
    )

    return {
        "ok": True,
        "message": {
            "id": message_ref.id,
            "conversationId": conversation_id,
            "authorId": author_ref,
            "authorName": author_label,
            "content": message_text,
        },
    }
